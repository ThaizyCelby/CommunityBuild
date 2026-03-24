# core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('home/', views.home, name='home'),          # was previously path('', views.home, name='home')
    path('professionals/', views.professional_list, name='professional_list'),
    path('professional/<int:pk>/', views.professional_detail, name='professional_detail'),
    path('projects/', views.project_list, name='project_list'),
    path('project/<int:pk>/', views.project_detail, name='project_detail'),
    path('posts/', views.post_list_all, name='post_list_all'),
    path('post/<int:profession_id>/', views.post_list, name='post_list'),
    path('post/<int:profession_id>/<int:post_id>/', views.post_detail, name='post_detail'),
    path('post/new/', views.create_post, name='create_post'),
    path('post/<int:post_id>/comment/', views.add_comment, name='add_comment'),
    path('register/', views.register, name='register'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('municipality/', views.municipality_dashboard, name='municipality_dashboard'),
    path('municipality/project/<int:project_id>/insights/', views.project_insights, name='project_insights'),
    path('municipality/inquiries/', views.inquiry_list, name='inquiry_list'),
    path('municipality/inquiry/<int:inquiry_id>/', views.inquiry_detail, name='inquiry_detail'),
    path('municipality/flagged/', views.flagged_content_list, name='flagged_content_list'),
    path('municipality/flagged/<int:flagged_id>/review/', views.flagged_content_review, name='flagged_review'),
    path('submit-inquiry/', views.submit_inquiry, name='submit_inquiry'),
    path('my-recommendations/', views.professional_recommendations, name='professional_recommendations'),
    path('municipality/recommendations/', views.project_recommendations, name='project_recommendations'),
    path('my-recommendations/', views.professional_recommendations, name='professional_recommendations'),
    path('municipality/project/new/', views.project_create, name='project_create'),
    path('my-inquiries/', views.my_inquiries, name='my_inquiries'),
    path('project/<int:project_id>/bid/', views.bid_create, name='bid_create'),
    path('my-bids/', views.my_bids, name='my_bids'),
    path('bid/<int:bid_id>/', views.bid_detail, name='bid_detail'),
    path('municipality/bids/', views.municipality_bids, name='municipality_bids'),
    path('municipality/bid/<int:bid_id>/review/', views.review_bid, name='review_bid'),
]