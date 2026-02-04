import string
import random
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import login as auth_login, authenticate, logout as auth_logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from openpyxl import Workbook
from .models import User, Mahasiswa, Dosen, Kelas, Pengaturan, HasilKuis, ProgresAktivitas, Aktivitas, Materi
from django.utils import timezone
from django.db.models import Avg, Count, Q, Max
from datetime import datetime
from django.utils.dateparse import parse_datetime
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt


def get_config():
    config, created = Pengaturan.objects.get_or_create(id=1)
    return config

def generate_token(length=6):
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def landing(request):
    if request.user.is_authenticated:
        if request.user.role == User.IS_DOSEN:
            return redirect('dash_dosen')
        elif request.user.role == User.IS_MAHASISWA:
            return redirect('dash_mhs')
    return render(request, 'landing.html', {'active_page': 'landing'})

def materi(request):
    return render(request, 'materi.html', {'active_page': 'materi'})

def petunjuk(request):
    return render(request, 'petunjuk.html', {'active_page': 'petunjuk'})

def tentang(request):
    return render(request, 'tentang.html', {'active_page': 'tentang'})

def reg_mahasiswa(request):
    if request.method == 'POST':
        nama = request.POST.get('nama')
        nim = request.POST.get('nim')
        email = request.POST.get('email')
        password = request.POST.get('password')
        token = request.POST.get('token')
        try:
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Email sudah terdaftar.')
                return render(request, 'reg_mahasiswa.html')
            
            if Mahasiswa.objects.filter(nim=nim).exists():
                messages.error(request, 'NIM sudah terdaftar.')
                return render(request, 'reg_mahasiswa.html')
            
            kelas = Kelas.objects.get(token=token)
            
            user = User(
                username=email, 
                email=email, 
                role=User.IS_MAHASISWA
            )
            user.set_password(password)
            user.save()
            
            Mahasiswa.objects.create(
                user=user, 
                nama_lengkap=nama, 
                nim=nim, 
                kelas=kelas
            )
            messages.success(request, 'Registrasi berhasil, silakan login.')
            return redirect('login')
        except Kelas.DoesNotExist:
            messages.error(request, 'Token kelas tidak valid.')
        except Exception as e:
            messages.error(request, f'Terjadi kesalahan: {str(e)}')
    return render(request, 'reg_mahasiswa.html')

def reg_dosen(request):
    if request.method == 'POST':
        nama = request.POST.get('nama')
        nip = request.POST.get('nip')
        email = request.POST.get('email')
        password = request.POST.get('password')
        try:
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Email sudah terdaftar.')
                return render(request, 'reg_dosen.html')

            if Dosen.objects.filter(nip=nip).exists():
                messages.error(request, 'NIP sudah terdaftar.')
                return render(request, 'reg_dosen.html')

            user = User(
                username=email, 
                email=email, 
                role=User.IS_DOSEN
            )
            user.set_password(password)
            user.save()

            Dosen.objects.create(user=user, nama_lengkap=nama, nip=nip)
            messages.success(request, 'Registrasi dosen berhasil.')
            return redirect('login')
        except Exception as e:
            messages.error(request, f'Terjadi kesalahan: {str(e)}')
    return render(request, 'reg_dosen.html')

def login(request):
    if request.method == 'POST':
        email_input = request.POST.get('email')
        password_input = request.POST.get('password')
        user = authenticate(request, username=email_input, password=password_input)
        if user is not None:
            auth_login(request, user)
            if user.role == User.IS_DOSEN:
                return redirect('dash_dosen')
            elif user.role == User.IS_MAHASISWA:
                return redirect('dash_mhs')
            else:
                return redirect('landing')
        messages.error(request, 'Email atau password salah.')
    return render(request, 'login.html')

def logout(request):
    auth_logout(request)
    return redirect('landing')

@login_required
def dash_dosen(request):
    if request.user.role != User.IS_DOSEN:
        return redirect('landing')

    dosen = request.user.dosen_profile
    config = get_config()

    if request.method == 'POST' and 'update_kkm' in request.POST:
        new_kkm = request.POST.get('kkm')
        if new_kkm:
            config.kkm = int(new_kkm)
            config.save()
            messages.success(request, f"Nilai KKM berhasil diperbarui menjadi {new_kkm}")
            return redirect('dash_dosen')

    mhs_queryset = Mahasiswa.objects.filter(kelas__dosen=dosen).select_related('user', 'kelas')
    total_kelas = Kelas.objects.filter(dosen=dosen).count()
    
    kelas_id = request.GET.get('kelas_id')
    if kelas_id:
        mhs_queryset = mhs_queryset.filter(kelas_id=kelas_id)

    total_mhs = mhs_queryset.count()
    mhs_rendah = 0
    total_aktivitas = Aktivitas.objects.count()
    mhs_selesai_count = 0

    for mhs in mhs_queryset:
        res_skor = HasilKuis.objects.filter(mahasiswa=mhs).aggregate(skor_tertinggi=Max('skor'))
        max_skor = res_skor.get('skor_tertinggi') or 0
        
        if 0 < max_skor < config.kkm:
            mhs_rendah += 1
        
        selesai = ProgresAktivitas.objects.filter(mahasiswa=mhs).count()
        persen = int((selesai / total_aktivitas * 100)) if total_aktivitas > 0 else 0
        mhs.progres_persen = persen
        
        if persen == 100:
            mhs_selesai_count += 1
        
        mhs.display_name = mhs.nama_lengkap if mhs.nama_lengkap else mhs.user.username

    top_mahasiswa = sorted(mhs_queryset, key=lambda x: getattr(x, 'progres_persen', 0), reverse=True)[:5]

    context = {
        'total_mhs': total_mhs,
        'total_kelas': total_kelas,
        'mhs_selesai': mhs_selesai_count,
        'mhs_dibawah_kkm': mhs_rendah,
        'top_mahasiswa': top_mahasiswa,
        'daftar_kelas': Kelas.objects.filter(dosen=dosen),
        'kkm': config.kkm,
    }
    return render(request, 'dosen/dash-dosen.html', context)

@login_required
def data_kelas(request):
    if request.user.role != User.IS_DOSEN:
        return redirect('landing')
    dosen = request.user.dosen_profile
    if request.method == 'POST':
        nama = request.POST.get('nama_kelas')
        angkatan = request.POST.get('angkatan')
        token = generate_token()
        Kelas.objects.create(dosen=dosen, nama_kelas=nama, angkatan=angkatan, token=token)
        messages.success(request, f'Kelas {nama} berhasil dibuat!')
        return redirect('data_kelas')
    daftar_kelas = Kelas.objects.filter(dosen=dosen)
    return render(request, 'dosen/data-kelas.html', {'daftar_kelas': daftar_kelas})

@login_required
def hapus_kelas(request, id):
    if request.user.role != User.IS_DOSEN:
        return redirect('landing')
    kelas = get_object_or_404(Kelas, id=id, dosen=request.user.dosen_profile)
    nama_kelas = kelas.nama_kelas
    kelas.delete()
    messages.success(request, f'Kelas "{nama_kelas}" berhasil dihapus.')
    return redirect('data_kelas')

@login_required
def data_mhs(request):
    if request.user.role != User.IS_DOSEN:
        return redirect('landing')
    dosen = request.user.dosen_profile
    query = request.GET.get('q', '')
    kelas_id = request.GET.get('kelas', '')
    per_page = request.GET.get('per_page', 10)
    daftar_mahasiswa_all = Mahasiswa.objects.filter(kelas__dosen=dosen).select_related('kelas').order_by('nama_lengkap')
    if query:
        daftar_mahasiswa_all = daftar_mahasiswa_all.filter(
            Q(nama_lengkap__icontains=query) | Q(nim__icontains=query)
        )
    if kelas_id:
        daftar_mahasiswa_all = daftar_mahasiswa_all.filter(kelas_id=kelas_id)
    paginator = Paginator(daftar_mahasiswa_all, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    start_index = page_obj.start_index() if page_obj.object_list else 0
    end_index = page_obj.end_index() if page_obj.object_list else 0
    total_data = paginator.count
    daftar_kelas = Kelas.objects.filter(dosen=dosen)
    context = {
        'daftar_mahasiswa': page_obj,
        'daftar_kelas': daftar_kelas,
        'start_index': start_index,
        'end_index': end_index,
        'total_data': total_data,
        'per_page': int(per_page),
    }
    return render(request, 'dosen/data-mhs.html', context)

@login_required
def export_mhs_excel(request):
    if request.user.role != User.IS_DOSEN:
        return HttpResponse("Unauthorized", status=401)

    dosen = request.user.dosen_profile
    kelas_id = request.GET.get('kelas')
    query = request.GET.get('q')

    mahasiswa_list = Mahasiswa.objects.filter(kelas__dosen=dosen).select_related('kelas')

    if kelas_id:
        mahasiswa_list = mahasiswa_list.filter(kelas_id=kelas_id)
    
    if query:
        mahasiswa_list = mahasiswa_list.filter(
            nama_lengkap__icontains=query
        ) | mahasiswa_list.filter(
            nim__icontains=query
        )

    mahasiswa_list = mahasiswa_list.order_by('nama_lengkap')

    wb = Workbook()
    ws = wb.active
    ws.title = "Data Mahasiswa"

    headers = ['No', 'Nama Mahasiswa', 'NIM', 'Kelas']
    ws.append(headers)

    for i, mhs in enumerate(mahasiswa_list, start=1):
        nama_kelas = mhs.kelas.nama_kelas if mhs.kelas else "Tanpa Kelas"
        ws.append([i, mhs.nama_lengkap, mhs.nim, nama_kelas])

    nama_file_tambahan = ""
    if kelas_id and mahasiswa_list.exists():
        nama_kelas = mahasiswa_list.first().kelas.nama_kelas
        nama_file_tambahan = f"_{nama_kelas}"

    filename = f"Data_Mahasiswa{nama_file_tambahan}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename={filename}'
    wb.save(response)
    
    return response

@login_required
def edit_mhs(request, mhs_id):
    if request.user.role != User.IS_DOSEN:
        return redirect('landing')
    
    mhs = get_object_or_404(Mahasiswa, id=mhs_id, kelas__dosen=request.user.dosen_profile)
    
    if request.method == 'POST':
        nama = request.POST.get('nama_lengkap')
        nim = request.POST.get('nim')
        password_baru = request.POST.get('password')
        
        if nama and nim:
            nim_terpakai = Mahasiswa.objects.filter(nim=nim).exclude(id=mhs_id).exists()
            if nim_terpakai:
                messages.error(request, f'NIM {nim} sudah terdaftar pada mahasiswa lain.')
            else:
                mhs.nama_lengkap = nama
                mhs.nim = nim
                mhs.save()

                if password_baru and password_baru.strip() != "":
                    user_mhs = mhs.user
                    user_mhs.set_password(password_baru)
                    user_mhs.save()
                    messages.success(request, f'Data dan password {nama} berhasil diperbarui.')
                else:
                    messages.success(request, f'Data {nama} berhasil diperbarui.')
        else:
            messages.error(request, 'Nama dan NIM wajib diisi.')
            
    return redirect('data_mhs')

@login_required
def hapus_mhs(request, mhs_id):
    if request.user.role != User.IS_DOSEN:
        return redirect('landing')
    mhs = get_object_or_404(Mahasiswa, id=mhs_id, kelas__dosen=request.user.dosen_profile)
    nama = mhs.nama_lengkap
    user_mhs = mhs.user
    mhs.delete()
    user_mhs.delete()
    messages.success(request, f'Mahasiswa {nama} berhasil dihapus.')
    return redirect('data_mhs')

@login_required
def progres_mhs(request):
    if request.user.role != User.IS_DOSEN:
        return redirect('landing')
    dosen = request.user.dosen_profile
    query = request.GET.get('q', '')
    kelas_id = request.GET.get('kelas', '')
    per_page = request.GET.get('per_page', 10)
    mhs_queryset = Mahasiswa.objects.filter(kelas__dosen=dosen).select_related('kelas').order_by('nama_lengkap')
    if query:
        mhs_queryset = mhs_queryset.filter(
            Q(nama_lengkap__icontains=query) | Q(nim__icontains=query)
        )
    if kelas_id:
        mhs_queryset = mhs_queryset.filter(kelas_id=kelas_id)
    for mhs in mhs_queryset:
        mhs.progres_belajar = mhs.hitung_progres_total()
    paginator = Paginator(mhs_queryset, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    total_data = paginator.count
    start_index = page_obj.start_index() if total_data > 0 else 0
    end_index = page_obj.end_index() if total_data > 0 else 0

    daftar_kelas = Kelas.objects.filter(dosen=dosen)
    context = {
        'daftar_mahasiswa': page_obj,
        'daftar_kelas': daftar_kelas,
        'per_page': int(per_page),
        'start_index': start_index,
        'end_index': end_index,
        'total_data': total_data,
    }
    return render(request, 'dosen/progres-mhs.html', context)

@login_required
def nilai_mhs(request):
    if request.user.role != User.IS_DOSEN:
        return redirect('landing')
        
    dosen = request.user.dosen_profile
    config = get_config()
    
    query = request.GET.get('q', '')
    kelas_id = request.GET.get('kelas', '')
    per_page = request.GET.get('per_page', 10)
    
    mhs_queryset = Mahasiswa.objects.filter(kelas__dosen=dosen).select_related('kelas').order_by('nama_lengkap')
    
    if query:
        mhs_queryset = mhs_queryset.filter(Q(nama_lengkap__icontains=query) | Q(nim__icontains=query))
    if kelas_id:
        mhs_queryset = mhs_queryset.filter(kelas_id=kelas_id)

    for mhs in mhs_queryset:
        rekap = {'k1': 0, 'k2': 0, 'k3': 0, 'k4': 0, 'k5': 0, 'k6': 0, 'evaluasi': 0}
        semua_hasil = HasilKuis.objects.filter(mahasiswa=mhs).order_by('waktu_selesai')
        
        riwayat_dict = {str(i): [] for i in range(1, 8)}
        counts = {str(i): 0 for i in range(1, 8)}
        
        for h in semua_hasil:
            num = str(h.nomor_kuis)
            counts[num] += 1
            
            key_rekap = 'evaluasi' if h.nomor_kuis == 7 else f'k{h.nomor_kuis}'
            if h.skor > rekap.get(key_rekap, 0):
                rekap[key_rekap] = h.skor
            
            raw_jawaban = h.get_list_jawaban()
            if isinstance(raw_jawaban, str):
                try:
                    jawaban_asli = json.loads(raw_jawaban)
                except:
                    jawaban_asli = []
            else:
                jawaban_asli = raw_jawaban

            limit_soal = 20 if h.nomor_kuis == 7 else 10
            jawaban_clean = []
            for jwb in jawaban_asli[:limit_soal]:
                if jwb is True or jwb == 1 or str(jwb).lower() == 'true':
                    jawaban_clean.append(True)
                else:
                    jawaban_clean.append(False)
            
            riwayat_dict[num].append({
                'percobaan_ke': counts[num],
                'waktu_selesai': h.waktu_selesai,
                'waktu_mulai': h.waktu_mulai,
                'skor': h.skor,
                'lulus': h.skor >= config.kkm,
                'detail_jawaban': jawaban_clean
            })
            
        mhs.nilai_rekap = rekap
        mhs.riwayat_per_kuis = riwayat_dict

        def get_stats(nomor, jml_soal):
            stats = [0] * jml_soal
            percobaan = HasilKuis.objects.filter(mahasiswa=mhs, nomor_kuis=nomor)
            total = percobaan.count()
            if total > 0:
                for p in percobaan:
                    list_raw = p.get_list_jawaban()
                    if isinstance(list_raw, str):
                        try:
                            list_jwb = json.loads(list_raw)
                        except:
                            list_jwb = []
                    else:
                        list_jwb = list_raw

                    for idx in range(jml_soal):
                        if idx < len(list_jwb):
                            val = list_jwb[idx]
                            if val is True or val == 1 or str(val).lower() == 'true':
                                stats[idx] += 1
                return [round((s/total)*100) for s in stats]
            return [0] * jml_soal

        mhs.persentase_k1 = get_stats(1, 10)
        mhs.persentase_k2 = get_stats(2, 10)
        mhs.persentase_k3 = get_stats(3, 10)
        mhs.persentase_k4 = get_stats(4, 10)
        mhs.persentase_k5 = get_stats(5, 10)
        mhs.persentase_k6 = get_stats(6, 10)
        mhs.persentase_evaluasi = get_stats(7, 20)

    paginator = Paginator(mhs_queryset, per_page)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    
    context = {
        'daftar_mahasiswa': page_obj,
        'daftar_kelas': Kelas.objects.filter(dosen=dosen),
        'kkm': config.kkm,
        'total_data': paginator.count,
        'per_page': int(per_page),
    }
    return render(request, 'dosen/nilai-mhs.html', context)

@login_required
def export_nilai_excel(request):
    if request.user.role != User.IS_DOSEN:
        return HttpResponse("Unauthorized", status=401)

    dosen = request.user.dosen_profile
    
    kelas_id = request.GET.get('kelas')
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Nilai Mahasiswa"

    headers = ['No', 'Nama Mahasiswa', 'NIM', 'Kelas', 'Kuis 1', 'Kuis 2', 'Kuis 3', 'Kuis 4', 'Kuis 5', 'Kuis 6', 'Evaluasi']
    ws.append(headers)

    mahasiswa_list = Mahasiswa.objects.filter(kelas__dosen=dosen).select_related('kelas')

    if kelas_id:
        mahasiswa_list = mahasiswa_list.filter(kelas_id=kelas_id)

    mahasiswa_list = mahasiswa_list.order_by('nama_lengkap')

    for idx, mhs in enumerate(mahasiswa_list, 1):
        rekap = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0}
        
        nilai_tertinggi = HasilKuis.objects.filter(mahasiswa=mhs).values('nomor_kuis').annotate(skor_max=Max('skor'))
        
        for n in nilai_tertinggi:
            rekap[n['nomor_kuis']] = n['skor_max']

        row = [
            idx,
            mhs.nama_lengkap,
            mhs.nim,
            mhs.kelas.nama_kelas if mhs.kelas else "-",
            rekap[1],
            rekap[2],
            rekap[3],
            rekap[4],
            rekap[5],
            rekap[6],
            rekap[7]
        ]
        ws.append(row)

    nama_file_tambahan = ""
    if kelas_id and mahasiswa_list.exists():
        nama_kelas = mahasiswa_list.first().kelas.nama_kelas
        nama_file_tambahan = f"_{nama_kelas}"

    filename = f"Nilai_Mahasiswa{nama_file_tambahan}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename={filename}'
    wb.save(response)
    return response

def get_user_progress(user):
    if hasattr(user, 'mahasiswa_profile'):
        mhs = user.mahasiswa_profile
        progres = ProgresAktivitas.objects.filter(mahasiswa=mhs, status_selesai=True)
        return list(progres.values_list('aktivitas__slug', flat=True))
    return []

def is_materi_accessible(mhs, nomor_kuis_sebelumnya, current_slug):
    if ProgresAktivitas.objects.filter(mahasiswa=mhs, aktivitas__slug=current_slug, status_selesai=True).exists():
        return True
    if nomor_kuis_sebelumnya == 0:
        return True
    return check_lulus(mhs, nomor_kuis_sebelumnya)

def check_lulus(mhs, nomor_kuis):
    config = get_config()
    kkm = config.kkm
    override_admin = ProgresAktivitas.objects.filter(
        mahasiswa=mhs, 
        aktivitas__slug=f'kuis-{nomor_kuis}', 
        status_selesai=True
    ).exists()
    if override_admin:
        return True
    return HasilKuis.objects.filter(mahasiswa=mhs, nomor_kuis=nomor_kuis, skor__gte=kkm).exists()

@login_required
def dash_mhs(request):
    if request.user.role != User.IS_MAHASISWA:
        return redirect('landing')

    mhs = request.user.mahasiswa_profile
    config = get_config()
    
    semua_hasil = HasilKuis.objects.filter(mahasiswa=mhs)
    
    nilai_kuis = {f'kuis_{i}': 0 for i in range(1, 7)}
    lulus_kuis = {f'kuis_{i}': False for i in range(1, 7)}
    nilai_evaluasi = 0
    lulus_evaluasi = False

    rekap_nilai = semua_hasil.values('nomor_kuis').annotate(skor_max=Max('skor'))

    for item in rekap_nilai:
        nomor = item['nomor_kuis']
        skor_tertinggi = item['skor_max']
        is_lulus = skor_tertinggi >= config.kkm

        if nomor == 7:
            nilai_evaluasi = skor_tertinggi
            lulus_evaluasi = is_lulus
        else:
            key = f'kuis_{nomor}'
            nilai_kuis[key] = skor_tertinggi
            lulus_kuis[key] = is_lulus

    total_aktivitas = Aktivitas.objects.count()
    aktivitas_selesai = ProgresAktivitas.objects.filter(mahasiswa=mhs, status_selesai=True).count()
    progress_percent = int((aktivitas_selesai / total_aktivitas * 100)) if total_aktivitas > 0 else 0

    selesai_slugs = ProgresAktivitas.objects.filter(
        mahasiswa=mhs, 
        status_selesai=True
    ).values_list('aktivitas__slug', flat=True)

    context = {
        'nilai_kuis': nilai_kuis,
        'lulus_kuis': lulus_kuis,
        'nilai_evaluasi': nilai_evaluasi,
        'lulus_evaluasi': lulus_evaluasi,
        'progress_percent': progress_percent,
        'selesai_slugs': selesai_slugs,
    }
    return render(request, 'mhs/dash-mhs.html', context)

@login_required
def pengertian_citra(request):
    if request.user.role != User.IS_MAHASISWA: return redirect('landing')
    return render(request, 'mhs/pengertian-citra.html', {'selesai_slugs': get_user_progress(request.user)})

@login_required
def jenis_citra(request):
    if request.user.role != User.IS_MAHASISWA: return redirect('landing')
    return render(request, 'mhs/jenis-citra.html', {'selesai_slugs': get_user_progress(request.user)})

@login_required
def ringkasan_citra(request):
    if request.user.role != User.IS_MAHASISWA: return redirect('landing')
    return render(request, 'mhs/ringkasan-citra.html', {'selesai_slugs': get_user_progress(request.user)})

@login_required
def kuis_1(request):
    if request.user.role != User.IS_MAHASISWA: return redirect('landing')
    return render(request, 'mhs/kuis-1.html', {'selesai_slugs': get_user_progress(request.user)})

@login_required
def pengertian_spatial(request):
    if request.user.role != User.IS_MAHASISWA: return redirect('landing')
    if not is_materi_accessible(request.user.mahasiswa_profile, 1, 'pengertian-spatial'):
        messages.warning(request, "Selesaikan Kuis 1 terlebih dahulu!")
        return redirect('dash_mhs')
    return render(request, 'mhs/pengertian-spatial.html', {'selesai_slugs': get_user_progress(request.user)})

@login_required
def spatial_frequency(request):
    if request.user.role != User.IS_MAHASISWA: return redirect('landing')
    if not is_materi_accessible(request.user.mahasiswa_profile, 1, 'spatial-frequency'): return redirect('dash_mhs')
    return render(request, 'mhs/spatial-frequency.html', {'selesai_slugs': get_user_progress(request.user)})

@login_required
def ringkasan2(request):
    if request.user.role != User.IS_MAHASISWA: return redirect('landing')
    if not is_materi_accessible(request.user.mahasiswa_profile, 1, 'ringkasan2'): return redirect('dash_mhs')
    return render(request, 'mhs/ringkasan2.html', {'selesai_slugs': get_user_progress(request.user)})

@login_required
def kuis_2(request):
    if request.user.role != User.IS_MAHASISWA: return redirect('landing')
    if not is_materi_accessible(request.user.mahasiswa_profile, 1, 'kuis-2'): return redirect('dash_mhs')
    return render(request, 'mhs/kuis-2.html', {'selesai_slugs': get_user_progress(request.user)})

@login_required
def k_konvolusi(request):
    if request.user.role != User.IS_MAHASISWA: return redirect('landing')
    if not is_materi_accessible(request.user.mahasiswa_profile, 2, 'k-konvolusi'):
        messages.warning(request, "Selesaikan Kuis 2 terlebih dahulu!")
        return redirect('dash_mhs')
    return render(request, 'mhs/k-konvolusi.html', {'selesai_slugs': get_user_progress(request.user)})

@login_required
def t_padding(request):
    if request.user.role != User.IS_MAHASISWA: return redirect('landing')
    if not is_materi_accessible(request.user.mahasiswa_profile, 2, 't-padding'): return redirect('dash_mhs')
    return render(request, 'mhs/t-padding.html', {'selesai_slugs': get_user_progress(request.user)})

@login_required
def normalisasi_citra(request):
    if request.user.role != User.IS_MAHASISWA: return redirect('landing')
    if not is_materi_accessible(request.user.mahasiswa_profile, 2, 'normalisasi-citra'): return redirect('dash_mhs')
    return render(request, 'mhs/normalisasi-citra.html', {'selesai_slugs': get_user_progress(request.user)})

@login_required
def ringkasan3(request):
    if request.user.role != User.IS_MAHASISWA: return redirect('landing')
    if not is_materi_accessible(request.user.mahasiswa_profile, 2, 'ringkasan3'): return redirect('dash_mhs')
    return render(request, 'mhs/ringkasan3.html', {'selesai_slugs': get_user_progress(request.user)})

@login_required
def kuis_3(request):
    if request.user.role != User.IS_MAHASISWA: return redirect('landing')
    if not is_materi_accessible(request.user.mahasiswa_profile, 2, 'kuis-3'): return redirect('dash_mhs')
    return render(request, 'mhs/kuis-3.html', {'selesai_slugs': get_user_progress(request.user)})

@login_required
def sl_filters(request):
    if request.user.role != User.IS_MAHASISWA: return redirect('landing')
    if not is_materi_accessible(request.user.mahasiswa_profile, 3, 'sl-filters'):
        messages.warning(request, "Selesaikan Kuis 3 terlebih dahulu!")
        return redirect('dash_mhs')
    return render(request, 'mhs/sl-filters.html', {'selesai_slugs': get_user_progress(request.user)})

@login_required
def sn_filters(request):
    if request.user.role != User.IS_MAHASISWA: return redirect('landing')
    if not is_materi_accessible(request.user.mahasiswa_profile, 3, 'sn-filters'): return redirect('dash_mhs')
    return render(request, 'mhs/sn-filters.html', {'selesai_slugs': get_user_progress(request.user)})

@login_required
def ringkasan4(request):
    if request.user.role != User.IS_MAHASISWA: return redirect('landing')
    if not is_materi_accessible(request.user.mahasiswa_profile, 3, 'ringkasan4'): return redirect('dash_mhs')
    return render(request, 'mhs/ringkasan4.html', {'selesai_slugs': get_user_progress(request.user)})

@login_required
def kuis_4(request):
    if request.user.role != User.IS_MAHASISWA: return redirect('landing')
    if not is_materi_accessible(request.user.mahasiswa_profile, 3, 'kuis-4'): return redirect('dash_mhs')
    return render(request, 'mhs/kuis-4.html', {'selesai_slugs': get_user_progress(request.user)})

@login_required
def sharp_citra(request):
    if request.user.role != User.IS_MAHASISWA: return redirect('landing')
    if not is_materi_accessible(request.user.mahasiswa_profile, 4, 'sharp-citra'):
        messages.warning(request, "Selesaikan Kuis 4 terlebih dahulu!")
        return redirect('dash_mhs')
    return render(request, 'mhs/sharp-citra.html', {'selesai_slugs': get_user_progress(request.user)})

@login_required
def um_highboost(request):
    if request.user.role != User.IS_MAHASISWA: return redirect('landing')
    if not is_materi_accessible(request.user.mahasiswa_profile, 4, 'um-highboost'): return redirect('dash_mhs')
    return render(request, 'mhs/um-highboost.html', {'selesai_slugs': get_user_progress(request.user)})

@login_required
def ringkasan5(request):
    if request.user.role != User.IS_MAHASISWA: return redirect('landing')
    if not is_materi_accessible(request.user.mahasiswa_profile, 4, 'ringkasan5'): return redirect('dash_mhs')
    return render(request, 'mhs/ringkasan5.html', {'selesai_slugs': get_user_progress(request.user)})

@login_required
def kuis_5(request):
    if request.user.role != User.IS_MAHASISWA: return redirect('landing')
    if not is_materi_accessible(request.user.mahasiswa_profile, 4, 'kuis-5'): return redirect('dash_mhs')
    return render(request, 'mhs/kuis-5.html', {'selesai_slugs': get_user_progress(request.user)})

@login_required
def gray_biner(request):
    if request.user.role != User.IS_MAHASISWA: return redirect('landing')
    if not is_materi_accessible(request.user.mahasiswa_profile, 5, 'gray-biner'):
        messages.warning(request, "Selesaikan Kuis 5 terlebih dahulu!")
        return redirect('dash_mhs')
    return render(request, 'mhs/gray-biner.html', {'selesai_slugs': get_user_progress(request.user)})

@login_required
def prak_konvolusi(request):
    if request.user.role != User.IS_MAHASISWA: return redirect('landing')
    if not is_materi_accessible(request.user.mahasiswa_profile, 5, 'prak-konvolusi'): return redirect('dash_mhs')
    return render(request, 'mhs/prak-konvolusi.html', {'selesai_slugs': get_user_progress(request.user)})

@login_required
def prak_smooth(request):
    if request.user.role != User.IS_MAHASISWA: return redirect('landing')
    if not is_materi_accessible(request.user.mahasiswa_profile, 5, 'prak-smooth'): return redirect('dash_mhs')
    return render(request, 'mhs/prak-smooth.html', {'selesai_slugs': get_user_progress(request.user)})

@login_required
def prak_sharp(request):
    if request.user.role != User.IS_MAHASISWA: return redirect('landing')
    if not is_materi_accessible(request.user.mahasiswa_profile, 5, 'prak-sharp'): return redirect('dash_mhs')
    return render(request, 'mhs/prak-sharp.html', {'selesai_slugs': get_user_progress(request.user)})

@login_required
def ringkasan6(request):
    if request.user.role != User.IS_MAHASISWA: return redirect('landing')
    if not is_materi_accessible(request.user.mahasiswa_profile, 5, 'ringkasan6'): return redirect('dash_mhs')
    return render(request, 'mhs/ringkasan6.html', {'selesai_slugs': get_user_progress(request.user)})

@login_required
def evaluasi(request):
    if request.user.role != User.IS_MAHASISWA: return redirect('landing')
    return render(request, 'mhs/evaluasi.html', {'selesai_slugs': get_user_progress(request.user)})

@login_required
def update_progres(request, slug=None):
    if request.method == 'POST':
        try:
            if not slug:
                data = json.loads(request.body)
                slug = data.get('slug')
            if not slug:
                return JsonResponse({'status': 'error', 'message': 'Slug tidak ditemukan'}, status=400)
            mhs = getattr(request.user, 'mahasiswa_profile', None)
            aktivitas = get_object_or_404(Aktivitas, slug=slug)
            progres, created = ProgresAktivitas.objects.update_or_create(
                mahasiswa=mhs, aktivitas=aktivitas,
                defaults={'status_selesai': True, 'tgl_selesai': timezone.now()}
            )
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)


def kalkulasi_skor_v2(jawaban_siswa, kunci_jawaban):
    benar_list = []
    benar_count = 0
    for i in range(len(kunci_jawaban)):
        is_benar = False
        if i < len(jawaban_siswa) and jawaban_siswa[i] is not None:
            try:
                if int(jawaban_siswa[i]) == kunci_jawaban[i]:
                    benar_count += 1
                    is_benar = True
            except (ValueError, TypeError):
                pass
        benar_list.append(is_benar)
    skor = int((benar_count / len(kunci_jawaban)) * 100)
    return skor, benar_list

def simpan_hasil_kuis_v2(mhs, nomor, skor, detail_jwb, mulai, selesai):
    config = get_config()
    kkm = config.kkm if config else 70
    lulus = skor >= kkm
    
    # Perbaikan parsing tanggal yang lebih tangguh
    def safe_parse(dt_str):
        if not dt_str or not isinstance(dt_str, str):
            return timezone.now()
        try:
            return parse_datetime(dt_str.replace(' ', 'T')) or timezone.now()
        except:
            return timezone.now()

    dt_mulai = safe_parse(mulai)
    dt_selesai = safe_parse(selesai)
    
    limit_soal = 20 if nomor == 7 else 10
    detail_jwb_fixed = detail_jwb[:limit_soal]
    
    HasilKuis.objects.create(
        mahasiswa=mhs, 
        nomor_kuis=nomor,
        skor=skor,
        detail_jawaban=json.dumps(detail_jwb_fixed),
        waktu_mulai=dt_mulai,
        waktu_selesai=dt_selesai,
    )
    
    if lulus:
        slug_kuis = f'kuis-{nomor}' if nomor < 7 else 'evaluasi'
        aktivitas = Aktivitas.objects.filter(slug=slug_kuis).first()
        if aktivitas:
            ProgresAktivitas.objects.update_or_create(
                mahasiswa=mhs, aktivitas=aktivitas,
                defaults={'status_selesai': True, 'tgl_selesai': timezone.now()}
            )
    return lulus

@csrf_exempt
@login_required
def cek_nilai_kuis_1(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            kunci = [2, 1, 0, 4, 3, 1, 3, 0, 2, 4]
            
            try:
                mhs = request.user.mahasiswa_profile
            except AttributeError:
                return JsonResponse({'error': 'Profile mahasiswa tidak ditemukan'}, status=400)

            skor, detail = kalkulasi_skor_v2(data.get('jawaban_siswa'), kunci)
            lulus = simpan_hasil_kuis_v2(mhs, 1, skor, detail, data.get('waktu_mulai'), data.get('waktu_selesai'))
            return JsonResponse({'skor': skor, 'lulus': lulus})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request'}, status=405)

@csrf_exempt
@login_required
def cek_nilai_kuis_2(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            kunci = [0, 1, 2, 1, 4, 3, 0, 4, 2, 3]
            mhs = request.user.mahasiswa_profile
            skor, detail = kalkulasi_skor_v2(data.get('jawaban_siswa'), kunci)
            lulus = simpan_hasil_kuis_v2(mhs, 2, skor, detail, data.get('waktu_mulai'), data.get('waktu_selesai'))
            return JsonResponse({'skor': skor, 'lulus': lulus})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request'}, status=405)

@csrf_exempt
@login_required
def cek_nilai_kuis_3(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            kunci = [0, 2, 1, 3, 0, 4, 2, 1, 3, 4]
            mhs = request.user.mahasiswa_profile
            skor, detail = kalkulasi_skor_v2(data.get('jawaban_siswa'), kunci)
            lulus = simpan_hasil_kuis_v2(mhs, 3, skor, detail, data.get('waktu_mulai'), data.get('waktu_selesai'))
            return JsonResponse({'skor': skor, 'lulus': lulus})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request'}, status=405)

@csrf_exempt
@login_required
def cek_nilai_kuis_4(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            kunci = [2, 3, 1, 4, 2, 3, 0, 4, 0, 1]
            mhs = request.user.mahasiswa_profile
            skor, detail = kalkulasi_skor_v2(data.get('jawaban_siswa'), kunci)
            lulus = simpan_hasil_kuis_v2(mhs, 4, skor, detail, data.get('waktu_mulai'), data.get('waktu_selesai'))
            return JsonResponse({'skor': skor, 'lulus': lulus})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request'}, status=405)

@csrf_exempt
@login_required
def cek_nilai_kuis_5(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            kunci = [1, 4, 0, 3, 0, 3, 2, 2, 4, 3]
            mhs = request.user.mahasiswa_profile
            skor, detail = kalkulasi_skor_v2(data.get('jawaban_siswa'), kunci)
            lulus = simpan_hasil_kuis_v2(mhs, 5, skor, detail, data.get('waktu_mulai'), data.get('waktu_selesai'))
            return JsonResponse({'skor': skor, 'lulus': lulus})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request'}, status=405)

@csrf_exempt
@login_required
def cek_nilai_evaluasi(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            kunci = [1, 4, 3, 1, 2, 4, 0, 3, 2, 2, 0, 4, 1, 0, 0, 1, 3, 2, 3, 4]
            mhs = request.user.mahasiswa_profile
            skor, detail = kalkulasi_skor_v2(data.get('jawaban_siswa'), kunci)
            lulus = simpan_hasil_kuis_v2(mhs, 7, skor, detail, data.get('waktu_mulai'), data.get('waktu_selesai'))
            return JsonResponse({'skor': skor, 'lulus': lulus})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request'}, status=405)





