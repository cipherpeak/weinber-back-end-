

from django.urls import path
from .views import *

urlpatterns = [
    path('notes/', NoteListView.as_view(), name='note-list'),
    path('notes/<int:note_id>/', NoteDetailView.as_view(), name='note-detail'),
    path('notes/<int:note_id>/edit/', NoteEditView.as_view(), name='note-edit'),
    path('notes/<int:note_id>/delete/', NoteDeleteView.as_view(), name='note-delete'),
]
