from django.urls import path
from . import views
from django.urls import re_path
from sms.views import(
    Categorieslistview,
     
    Topicslistview,
    #   Topic_list,
    
    # dashboard url
       Category,
       Table,
       Homepage,
    #    Homepage1,
       Homepage2,
      #  Homepage,
     
       AlertView,
       Courseslistview,

    #    end
    
      Courseslistdescview,
      # Topicsdetailview,
      Feedbackformview,
      Commentlistview,
      Commentlistviewsuccess,
      UserProfilelistview,
      UserProfileForm,
      Certificates,
      Certdetaillistview,
      UserProfileUpdateForm,
      Admin_result,
      Admin_detail_view,
      Bloglistview,
      Blogdetaillistview,
      Baseblogview,
      BlogcommentCreateView,
      PhotoGallery,
      Paymentdesc,
      PaymentSucess,
      Ebooks,
      GalleryDetailView,
      DirectorsView,
      Clubs,
      ClubsListView,
      gotopdfconfirmpage,
      pdfpaymentconfirmation,
      PDFDocumentDetailView,
      MarkTopicCompleteView,
      DigitalForm, PDFGalleryView, ManagementView,
   
      
) 

from .views import AboutUsView,AwardView

app_name = 'sms'

urlpatterns = [
    

    # path('', Categorieslistview.as_view(), name='categorieslist'),
    path('pdf-gallery/', PDFGalleryView.as_view(), name='pdf_gallery'),
    path('directors/', DirectorsView.as_view(), name='directors'),
    path('managements/', ManagementView.as_view(), name='managements'),
    path('digital-form/', DigitalForm.as_view(), name='digital_form'),
    path('about-us/', AboutUsView.as_view(), name='about_us'),
    path('awards/', AwardView.as_view(), name='awards'),
    path('ebooks/<int:pk>/', Ebooks.as_view(), name='ebooks'),
    path('gallery-detail/<int:pk>/', GalleryDetailView.as_view(), name='gallery_detail'),
    path('clubs/', ClubsListView.as_view(), name='clubs'),
    path('clubs-list/<int:pk>/', Clubs.as_view(), name='clubs_list'),
    # path('pdf_document_detail/<str:pk>/', pdf_document_detail.as_view(), name='pdf_document_detail'),
    path('pdfpaymentconfirmation/<str:pk>/', pdfpaymentconfirmation.as_view(), name='pdfpaymentconfirmation'),
    path('pdf_document_detail/<int:pk>/', PDFDocumentDetailView.as_view(), name='pdf_document_detail'),
    path('gotopdfconfirmpage/<int:pk>/', gotopdfconfirmpage.as_view(), name='gotopdfconfirmpage'),

    # new dashboard urls
    path('home', Category.as_view(), name='home'),
    path('course/<str:pk>/',  Paymentdesc.as_view(), name='course'),
    # re_path(r'^paymentdesc/(?P<course_name>[-\w]+)/$', Paymentdesc.as_view(), name='paymentdesc'),
    path('paymentsucess/<str:pk>/',  PaymentSucess.as_view(), name='paymentsucess'),
    path('table', Table.as_view(), name='table'),
    path('', Homepage.as_view(), name='homepage'),
    # path('homepage1', Homepage1.as_view(), name='homepage1'),
    # path('homepage', Homepage.as_view(), name='homepage'),
    
    path('alert', AlertView.as_view(), name='alert'),
    path('courseslist/<pk>/', Courseslistview.as_view(), name='courseslist'),
    path('admin_result', Admin_result.as_view(), name ='admin_result'),
    path('admin_result_detail_view/<pk>/', Admin_detail_view, name ='admin_result_detail_view'),
    path('userprofileform', UserProfileForm.as_view(), name ='userprofileform'),
    path('myprofile', UserProfilelistview.as_view(), name ='myprofile'),

    
    # path('certificates/<pk>/', views.Certificates, name ='certificates'),
    path('certificates/<pk>/', Certdetaillistview.as_view(), name='certificates'),
    path('bloglistview', Bloglistview.as_view(), name ='bloglistview'),
    path('blog/<slug:slug>/', Blogdetaillistview.as_view(), name='blogdetaillistview'),
    
    # end

    path('courseslistdesc/<pk>/', Courseslistdescview.as_view(), name='courseslistdesc'),
    path('topicslistview/<pk>/', Topicslistview.as_view(), name='topicslistview'),
    path('mark_topic_completed/', MarkTopicCompleteView.as_view(), name='mark_topic_completed'),

    # path('topicsdetailview/<slug:slug>/', Topicsdetailview.as_view(), name='topicsdetailview'),
    # path('signupview', signupview.as_view(), name ='signupview'),
    path('feedbackformview', Feedbackformview.as_view(), name ='feedbackformview'),
    path('commentlistview', Commentlistview.as_view(), name ='commentlistview'),
    path('commentlistviewsuccess', Commentlistviewsuccess.as_view(), name ='commentlistviewsuccess'),
    # path('topic', views.Topic_list, name="topic"),
    path('userprofileupdateform/<pk>/', UserProfileUpdateForm.as_view(), name ='userprofileupdateform'),
    path('baseview/<pk>/',  Baseblogview.as_view(), name='baseview'),
    path('blog/<slug:slug>/blogcommentform/', BlogcommentCreateView.as_view(), name ='blogcommentform'),
    
    # new pagination url
    # path("terms",views.KeywordListView.as_view(),name="terms"),
    # path("terms/<int:page>",views.listing,name="terms-by-page"),
    # path('terms.json/',views.listing_api, name='terms-api'),
    # path("faux",views.AllKeywordsView.as_view(),name="faux"),

 
]





