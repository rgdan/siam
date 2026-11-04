from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from api.models import User
from audit.models import AuditEntry
from collection_integrity.models import Piece, Photo
from collection_integrity.services import decommission_piece, loan_piece, return_piece, mark_missing, change_piece_state
from collection_integrity.reports import collection_report_data


class IntegratedCollectionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='integration@siam.local', full_name='Museólogo de prueba', role='museologo')
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def piece(self, title, state='stored'):
        piece = Piece.objects.create(title=title, state=state, location='Sala 1' if state == 'displayed' else '', object_type='Escultura', collection='Integrada')
        Photo.objects.create(piece=piece, name='Conservada', content=b'photo')
        return piece

    def test_all_persisted_lifecycle_states_match_report_and_consolidated_function(self):
        displayed = self.piece('Exhibición', 'displayed')
        stored = self.piece('Almacenamiento')
        loan = self.piece('Préstamo', 'displayed')
        stolen = self.piece('Robo', 'displayed')
        lost = self.piece('Extravío')
        inactive = self.piece('Baja')
        loan_piece(user=self.user, piece_id=loan.pk, recipient='Museo B', start_date='2026-01-01', end_date='2026-01-02')
        mark_missing(user=self.user, piece_id=stolen.pk, state='stolen', event_date=timezone.localdate(), confirmed=True)
        mark_missing(user=self.user, piece_id=lost.pk, state='lost', event_date=timezone.localdate(), confirmed=True)
        decommission_piece(user=self.user, piece_id=inactive.pk, reason='Motivo', confirmed=True)
        with self.assertNumQueries(1):
            report = collection_report_data(collection='Integrada')
        self.assertEqual(report['total'], 6)
        self.assertEqual(report['active'], 3)
        self.assertEqual(report['by_state'], {'displayed': 1, 'stored': 1, 'loaned': 1, 'missing': 2, 'decommissioned': 1})
        actual = self.client.get('/api/collection/report/?collection=Integrada').json()
        self.assertEqual(actual['by_state'], report['by_state'])
        self.assertEqual(actual['by_collection'], {'Integrada': 6})
        self.assertEqual(actual['by_object_type'], {'Escultura': 6})
        self.assertEqual(collection_report_data(state='stolen')['total'], 1)
        self.assertEqual(collection_report_data(state='lost')['total'], 1)
        self.assertEqual(collection_report_data(state='missing')['total'], 2)
        for piece in [displayed, stored, loan, stolen, lost, inactive]:
            self.assertEqual(piece.photos.count(), 1)

    def test_real_unavailable_states_reject_loans_and_baja_blocks_missing(self):
        for state in ['stolen', 'lost']:
            piece = self.piece(state)
            mark_missing(user=self.user, piece_id=piece.pk, state=state, event_date=timezone.localdate(), confirmed=True)
            response = self.client.post(f'/api/pieces/{piece.pk}/loan/', {'recipient': 'Museo', 'start_date': '2026-01-01', 'end_date': '2026-01-02'}, format='json')
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json()['detail'], 'cannot_loan_' + state)
            self.assertEqual(AuditEntry.objects.filter(entity='piece', entity_id=str(piece.pk)).count(), 1)
            decommission_piece(user=self.user, piece_id=piece.pk, reason='Baja posterior', confirmed=True)
            response = self.client.post(f'/api/pieces/{piece.pk}/missing/', {'state': state, 'event_date': str(timezone.localdate()), 'confirmed': True}, format='json')
            self.assertEqual(response.status_code, 400)
            piece.refresh_from_db()
            self.assertEqual(piece.state, 'decommissioned')
        self.assertEqual(collection_report_data()['by_state']['decommissioned'], 2)
        self.assertEqual(collection_report_data()['by_state']['missing'], 0)

    def test_decommissioned_piece_retains_loan_history_and_photos(self):
        piece = self.piece('Préstamo anterior', 'displayed')
        loan_piece(user=self.user, piece_id=piece.pk, recipient='Museo B', start_date='2026-01-01', end_date='2026-01-02')
        return_piece(user=self.user, piece_id=piece.pk)
        decommission_piece(user=self.user, piece_id=piece.pk, reason='Conservación', confirmed=True)
        detail = self.client.get(f'/api/pieces/{piece.pk}/').json()
        self.assertEqual(detail['state'], 'decommissioned')
        self.assertEqual(len(detail['photos']), 1)
        self.assertEqual(len(detail['history']), 3)
        self.assertEqual(detail['decommission_reason'], 'Conservación')
        self.assertEqual(detail['decommissioned_user'], self.user.full_name)
        self.assertTrue(detail['decommissioned_at'])
        self.assertTrue(any(entry['changes'].get('loan_to', {}).get('new') == 'Museo B' for entry in detail['history']))
        self.assertEqual(self.client.patch(f'/api/pieces/{piece.pk}/', {'title': 'No permitido'}, format='json').status_code, 400)
        photo = piece.photos.get()
        self.assertEqual(self.client.delete(f'/api/pieces/{piece.pk}/photos/{photo.pk}/').status_code, 400)
        self.assertEqual(piece.photos.count(), 1)

    def test_generic_state_helper_cannot_bypass_missing_or_return(self):
        piece = self.piece('No evadir devolución')
        loan_piece(user=self.user, piece_id=piece.pk, recipient='Museo B', start_date='2026-01-01', end_date='2026-01-02')
        from rest_framework.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            change_piece_state(user=self.user, piece_id=piece.pk, state='stored')
        piece.refresh_from_db()
        self.assertEqual(piece.state, 'loaned')
        return_piece(user=self.user, piece_id=piece.pk)
        self.assertEqual(collection_report_data()['by_state']['stored'], 1)

    def test_audit_failure_preserves_report_counts_and_previous_state(self):
        piece = self.piece('Rollback', 'displayed')
        before = collection_report_data()
        with patch('collection_integrity.services.record', side_effect=RuntimeError('Audit failed')):
            with self.assertRaises(RuntimeError):
                decommission_piece(user=self.user, piece_id=piece.pk, reason='Error', confirmed=True)
        piece.refresh_from_db()
        self.assertEqual((piece.state, piece.location, piece.decommissioned), ('displayed', 'Sala 1', False))
        self.assertEqual(collection_report_data()['by_state'], before['by_state'])
        self.assertFalse(AuditEntry.objects.filter(entity='piece').exists())


    def test_storage_location_is_saved_audited_and_preserved_on_other_edits(self):
        piece = self.piece('Ubicación de almacén')
        url = f'/api/pieces/{piece.pk}/'
        response = self.client.patch(url, {'location': 'Bodega A, estante 3'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['location'], 'Bodega A, estante 3')
        self.assertEqual(self.client.patch(url, {'title': 'Nuevo título'}, format='json').status_code, 200)
        piece.refresh_from_db()
        self.assertEqual((piece.state, piece.location), ('stored', 'Bodega A, estante 3'))
        self.assertTrue(AuditEntry.objects.filter(entity='piece', entity_id=str(piece.pk), changes__location__new='Bodega A, estante 3').exists())
        response = self.client.patch(url, {'state': 'displayed'}, format='json')
        self.assertEqual(response.status_code, 200)
        response = self.client.patch(url, {'state': 'stored'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['location'], 'Bodega A, estante 3')
        self.assertEqual(self.client.get(url).json()['location'], 'Bodega A, estante 3')

    def test_storage_creation_and_state_helper_accept_physical_location(self):
        payload = {key: 'Dato' for key in ['title', 'object_type', 'materials_techniques', 'inscriptions_marks', 'distinguishing_features', 'subject', 'date_period', 'author_maker']}
        payload.update(measurement_value='10', measurement_unit='cm', location='Bodega B')
        response = self.client.post('/api/pieces/', payload, format='json')
        self.assertEqual(response.status_code, 201)
        piece = Piece.objects.get(pk=response.json()['id'])
        self.assertEqual((piece.state, piece.location), ('stored', 'Bodega B'))
        change_piece_state(user=self.user, piece_id=piece.pk, state='stored', location='Bodega C')
        piece.refresh_from_db()
        self.assertEqual(piece.location, 'Bodega C')

    def test_storage_location_remains_optional_and_display_location_required(self):
        piece = self.piece('Sin ubicación registrada')
        url = f'/api/pieces/{piece.pk}/'
        self.assertEqual(self.client.patch(url, {'location': ''}, format='json').status_code, 200)
        self.assertEqual(self.client.patch(url, {'state': 'displayed'}, format='json').status_code, 400)
        self.assertEqual(self.client.patch(url, {'location': 'x' * 201}, format='json').status_code, 400)
