from django.contrib import admin
from .models import User, Dosen, Kelas, Mahasiswa, Materi, Aktivitas, ProgresAktivitas, Pengaturan, HasilKuis

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'get_nama_lengkap', 'role', 'is_staff', 'is_active')
    search_fields = ('email', 'mahasiswa_profile__nama_lengkap', 'dosen_profile__nama_lengkap')
    list_filter = ('role', 'is_staff', 'is_active')

    def get_nama_lengkap(self, obj):
        if obj.role == User.IS_MAHASISWA and hasattr(obj, 'mahasiswa_profile'):
            return obj.mahasiswa_profile.nama_lengkap
        elif obj.role == User.IS_DOSEN and hasattr(obj, 'dosen_profile'):
            return obj.dosen_profile.nama_lengkap
        return "-"
    get_nama_lengkap.short_description = 'Nama Lengkap'

@admin.register(Dosen)
class DosenAdmin(admin.ModelAdmin):
    list_display = ('nama_lengkap', 'nip', 'user_email')
    search_fields = ('nama_lengkap', 'nip', 'user__email')

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email Akun'

@admin.register(Kelas)
class KelasAdmin(admin.ModelAdmin):
    list_display = ('nama_kelas', 'angkatan', 'token', 'dosen')
    search_fields = ('nama_kelas', 'token', 'dosen__nama_lengkap')
    list_filter = ('angkatan',)

@admin.register(Mahasiswa)
class MahasiswaAdmin(admin.ModelAdmin):
    list_display = ('nama_lengkap', 'nim', 'kelas', 'user_email')
    search_fields = ('nama_lengkap', 'nim', 'user__email')
    list_filter = ('kelas', 'kelas__angkatan')

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email Akun'

@admin.register(Materi)
class MateriAdmin(admin.ModelAdmin):
    list_display = ('urutan', 'nama_materi')
    ordering = ('urutan',)

@admin.register(Aktivitas)
class AktivitasAdmin(admin.ModelAdmin):
    list_display = ('materi', 'urutan', 'nama_aktivitas', 'slug')
    list_filter = ('materi',)
    search_fields = ('nama_aktivitas',)
    prepopulated_fields = {'slug': ('nama_aktivitas',)}

@admin.register(ProgresAktivitas)
class ProgresAktivitasAdmin(admin.ModelAdmin):
    list_display = ('mahasiswa', 'aktivitas', 'status_selesai', 'tgl_selesai')
    list_filter = ('status_selesai', 'aktivitas', 'mahasiswa__kelas')
    search_fields = ('mahasiswa__nama_lengkap', 'aktivitas__nama_aktivitas')

@admin.register(Pengaturan)
class PengaturanAdmin(admin.ModelAdmin):
    list_display = ('pk', 'kkm')

@admin.register(HasilKuis)
class HasilKuisAdmin(admin.ModelAdmin):
    list_display = ('mahasiswa', 'nomor_kuis', 'skor', 'tanggal_pengerjaan')
    list_filter = ('nomor_kuis', 'mahasiswa__kelas')
    search_fields = ('mahasiswa__nama_lengkap',)