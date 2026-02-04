from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('materi/', views.materi, name='materi'),
    path('petunjuk/', views.petunjuk, name='petunjuk'),
    path('tentang/', views.tentang, name='tentang'),
    path('register/mahasiswa/', views.reg_mahasiswa, name='reg_mahasiswa'),
    path('register/dosen/', views.reg_dosen, name='reg_dosen'),
    path('register/login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),

    path('dash-dosen/', views.dash_dosen, name='dash_dosen'),
    path('dash-dosen/data-kelas/', views.data_kelas, name='data_kelas'),
    path('dash-dosen/hapus-kelas/<int:id>/', views.hapus_kelas, name='hapus_kelas'),
    path('dash-dosen/data-mhs/', views.data_mhs, name='data_mhs'),
    path('dosen/mahasiswa/edit/<int:mhs_id>/', views.edit_mhs, name='edit_mhs'),
    path('data-mhs/export/', views.export_mhs_excel, name='export_mhs_excel'),
    path('dosen/mahasiswa/hapus/<int:mhs_id>/', views.hapus_mhs, name='hapus_mhs'),
    path('dash-dosen/progres-mhs/', views.progres_mhs, name='progres_mhs'),
    path('dash-dosen/nilai-mhs/', views.nilai_mhs, name='nilai_mhs'),
    path('dash-dosen/nilai-mhs/export/', views.export_nilai_excel, name='export_nilai_excel'),

    path('dash-mhs/', views.dash_mhs, name='dash_mhs'),  
    
    path('materi/pengertian-citra/', views.pengertian_citra, name='pengertian_citra'),
    path('materi/jenis-citra/', views.jenis_citra, name='jenis_citra'),
    path('materi/ringkasan-citra/', views.ringkasan_citra, name='ringkasan_citra'),
    path('materi/kuis-1/', views.kuis_1, name='kuis_1'),
    path('api/cek-kuis-1/', views.cek_nilai_kuis_1, name='cek_nilai_kuis_1'),

    path('materi/pengertian-spatial/', views.pengertian_spatial, name='pengertian_spatial'),
    path('materi/spatial-frequency/', views.spatial_frequency, name='spatial_frequency'),
    path('materi/ringkasan2/', views.ringkasan2, name='ringkasan2'),
    path('materi/kuis-2/', views.kuis_2, name='kuis_2'),
    path('api/cek-kuis-2/', views.cek_nilai_kuis_2, name='cek_nilai_kuis_2'),

    path('materi/k-konvolusi/', views.k_konvolusi, name='k_konvolusi'),
    path('materi/t-padding/', views.t_padding, name='t_padding'),
    path('materi/normalisasi-citra/', views.normalisasi_citra, name='normalisasi_citra'),
    path('materi/ringkasan3/', views.ringkasan3, name='ringkasan3'),
    path('materi/kuis-3/', views.kuis_3, name='kuis_3'),
    path('api/cek-kuis-3/', views.cek_nilai_kuis_3, name='cek_nilai_kuis_3'),

    path('materi/sl-filters/', views.sl_filters, name='sl_filters'),
    path('materi/sn-filters/', views.sn_filters, name='sn_filters'),
    path('materi/ringkasan4/', views.ringkasan4, name='ringkasan4'),
    path('materi/kuis-4/', views.kuis_4, name='kuis_4'),
    path('api/cek-kuis-4/', views.cek_nilai_kuis_4, name='cek_nilai_kuis_4'),
    
    path('materi/sharp-citra/', views.sharp_citra, name='sharp_citra'),  
    path('materi/um-highboost/', views.um_highboost, name='um_highboost'),
    path('materi/ringkasan5/', views.ringkasan5, name='ringkasan5'),
    path('materi/kuis-5/', views.kuis_5, name='kuis_5'),
    path('api/cek-kuis-5/', views.cek_nilai_kuis_5, name='cek_nilai_kuis_5'),
     
    path('materi/gray-biner/', views.gray_biner, name='gray_biner'),
    path('materi/prak-konvolusi/', views.prak_konvolusi, name='prak_konvolusi'),
    path('materi/prak-smooth/', views.prak_smooth, name='prak_smooth'),
    path('materi/prak-sharp/', views.prak_sharp, name='prak_sharp'),
    path('materi/ringkasan6/', views.ringkasan6, name='ringkasan6'),
    
    path('materi/evaluasi/', views.evaluasi, name='evaluasi'),
    path('api/cek-evaluasi/', views.cek_nilai_evaluasi, name='cek_nilai_evaluasi'),

    path('api/update-progres/', views.update_progres, name='update_progres'),
]