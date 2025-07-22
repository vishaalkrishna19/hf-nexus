from django.urls import path
from . import views
from . import checkATS

urlpatterns = [
    path('hello/', views.hello_world, name='hello_world'),
    path('shortlist-candidates/', views.shortlist_candidates, name='shortlist_candidates'),
    path('export-excel/', views.export_to_excel, name='export_to_excel'),
    path('rank-resumes/', views.rank_resumes, name='rank_resumes'),  
    path('', views.parse_resume, name='parse_resume'),
    path('check-ats/', checkATS.check_ats_view, name='check_ats'),
    path('github-details/', views.github_details, name='github_details'),
    path('process-excel-drive-links/', views.process_excel_drive_links, name='process_excel_drive_links'),
]