import string
import random
import json
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify

class User(AbstractUser):
    IS_MAHASISWA = 'mahasiswa'
    IS_DOSEN = 'dosen'
    ROLE_CHOICES = (
        (IS_MAHASISWA, 'Mahasiswa'),
        (IS_DOSEN, 'Dosen'),
    )
    
    username = models.CharField(
        max_length=150,
        unique=True,
        help_text='Username otomatis menggunakan email.',
        validators=[], 
        error_messages={
            'unique': "Username ini sudah terdaftar.",
        },
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

class Dosen(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='dosen_profile')
    nama_lengkap = models.CharField(max_length=255)
    nip = models.CharField(max_length=30, unique=True)

    def __str__(self): 
        return self.nama_lengkap

class Kelas(models.Model):
    dosen = models.ForeignKey(Dosen, on_delete=models.CASCADE, related_name='daftar_kelas')
    nama_kelas = models.CharField(max_length=100)
    angkatan = models.CharField(max_length=10)
    token = models.CharField(max_length=6, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.token:
            char_set = string.ascii_uppercase + string.digits
            while True:
                new_token = ''.join(random.choices(char_set, k=6))
                if not Kelas.objects.filter(token=new_token).exists():
                    self.token = new_token
                    break
        super().save(*args, **kwargs)

    def __str__(self): 
        return self.nama_kelas

class Pengaturan(models.Model):
    kkm = models.IntegerField(default=75)

    class Meta:
        verbose_name_plural = "Pengaturan"

    def save(self, *args, **kwargs):
        self.pk = 1
        super(Pengaturan, self).save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

class Mahasiswa(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='mahasiswa_profile')
    nama_lengkap = models.CharField(max_length=255)
    nim = models.CharField(max_length=20, unique=True)
    kelas = models.ForeignKey(Kelas, on_delete=models.SET_NULL, null=True, related_name='mahasiswa_list')

    def hitung_progres_total(self):
        total = Aktivitas.objects.count()
        if total == 0: return 0
        selesai = ProgresAktivitas.objects.filter(mahasiswa=self, status_selesai=True).count()
        return int((selesai / total) * 100)

    def get_detail_progres(self):
        progres_data = {}
        all_aktivitas = Aktivitas.objects.all()
        selesai_user = ProgresAktivitas.objects.filter(mahasiswa=self, status_selesai=True).values_list('aktivitas__nama_aktivitas', flat=True)
        
        for akt in all_aktivitas:
            if akt.nama_aktivitas in selesai_user:
                progres_data[akt.nama_aktivitas] = "done"
            else:
                progres_data[akt.nama_aktivitas] = "lock"
        return json.dumps(progres_data)

    @property
    def detail_progres_json(self):
        return self.get_detail_progres()

    def __str__(self): 
        return self.nama_lengkap

class HasilKuis(models.Model):
    EVALUASI_AKHIR = 7
    mahasiswa = models.ForeignKey(Mahasiswa, on_delete=models.CASCADE, related_name='riwayat_kuis')
    nomor_kuis = models.IntegerField()
    skor = models.IntegerField()
    detail_jawaban = models.JSONField(default=list, blank=True)
    tanggal_pengerjaan = models.DateTimeField(auto_now_add=True)
    waktu_mulai = models.DateTimeField(null=True, blank=True)
    waktu_selesai = models.DateTimeField(null=True, blank=True)

    class Meta: 
        ordering = ['-tanggal_pengerjaan']
        verbose_name_plural = "Hasil Kuis & Evaluasi"

    def get_list_jawaban(self):
        return self.detail_jawaban

    def __str__(self):
        label = f"Kuis {self.nomor_kuis}" if self.nomor_kuis != self.EVALUASI_AKHIR else "Evaluasi Akhir"
        return f"{self.mahasiswa.nama_lengkap} - {label} (Skor: {self.skor})"

class Materi(models.Model):
    nama_materi = models.CharField(max_length=100)
    urutan = models.PositiveIntegerField()
    def __str__(self): 
        return f"{self.urutan}. {self.nama_materi}"
    class Meta: 
        verbose_name_plural = "Materi"
        ordering = ['urutan']

class Aktivitas(models.Model):
    materi = models.ForeignKey(Materi, on_delete=models.CASCADE, related_name='aktivitas')
    nama_aktivitas = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, null=True, blank=True)
    urutan = models.PositiveIntegerField()

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nama_aktivitas)
        super().save(*args, **kwargs)

    def __str__(self): 
        return f"{self.materi.urutan}.{self.urutan} {self.nama_aktivitas}"
    class Meta: 
        verbose_name_plural = "Aktivitas"
        ordering = ['materi__urutan', 'urutan']

class ProgresAktivitas(models.Model):
    mahasiswa = models.ForeignKey(Mahasiswa, on_delete=models.CASCADE, related_name='progres_aktivitas')
    aktivitas = models.ForeignKey(Aktivitas, on_delete=models.CASCADE)
    status_selesai = models.BooleanField(default=False)
    tgl_selesai = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('mahasiswa', 'aktivitas')
        verbose_name_plural = "Progres Aktivitas"

    def __str__(self):
        return f"{self.mahasiswa.nama_lengkap} - {self.aktivitas.nama_aktivitas}"