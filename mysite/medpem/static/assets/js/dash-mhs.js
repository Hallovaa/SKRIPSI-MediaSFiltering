// medpem/static/assets/js/dash-mhs.js
// Versi robust: deteksi path & highlight menu (Dashboard + Submenu)
// Pastikan file ini dimuat setelah bootstrap.bundle.min.js
document.addEventListener('DOMContentLoaded', function () {
  (function(){
    // Elemen utama
    const sidebar = document.getElementById('sidebar');
    const main = document.getElementById('main');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebarToggleIcon = document.getElementById('sidebarToggleIcon');
    const openBtn = document.getElementById('openBtn');

    // Util kecil
    const q = (sel) => document.querySelector(sel);
    const qa = (sel) => Array.from(document.querySelectorAll(sel));
    const safe = (fn) => { try { return fn(); } catch(e){ return null; } };

    // ---------- State sidebar (persist) ----------
    let collapsed = localStorage.getItem('sbCollapsed') === 'true';
    function applyState(isCollapsed){
      if(!sidebar || !main) return;
      if(isCollapsed){
        sidebar.classList.add('collapsed');
        main.classList.add('full');
        openBtn && openBtn.classList.add('visible');
        if(sidebarToggleIcon) sidebarToggleIcon.className = 'bi bi-chevron-right';
      } else {
        sidebar.classList.remove('collapsed');
        main.classList.remove('full');
        openBtn && openBtn.classList.remove('visible');
        if(sidebarToggleIcon) sidebarToggleIcon.className = 'bi bi-chevron-left';
      }
    }
    applyState(collapsed);

    sidebarToggle && sidebarToggle.addEventListener('click', ()=>{ collapsed = true; localStorage.setItem('sbCollapsed', true); applyState(true); });
    openBtn && openBtn.addEventListener('click', ()=>{ collapsed = false; localStorage.setItem('sbCollapsed', false); applyState(false); });

    // ---------- Collapse triggers: hanya 1 open ----------
    const triggers = qa('.collapse-trigger');
    function closeAllExcept(openId){
      triggers.forEach(t=>{
        const target = t.getAttribute('data-target');
        const el = document.querySelector(target);
        if(!el) return;
        if(target !== openId){
          safe(()=>bootstrap.Collapse.getOrCreateInstance(el).hide());
          t.classList.remove('parent-active');
          t.setAttribute('aria-expanded','false');
        } else {
          safe(()=>bootstrap.Collapse.getOrCreateInstance(el).show());
          t.classList.add('parent-active');
          t.setAttribute('aria-expanded','true');
        }
      });
    }
    triggers.forEach(t=>{
      t.addEventListener('click', function(e){
        e.preventDefault();
        const id = t.getAttribute('data-target');
        const el = document.querySelector(id);
        if(!el) return;
        const shown = el.classList.contains('show');
        if(shown){
          safe(()=>bootstrap.Collapse.getOrCreateInstance(el).hide());
          t.classList.remove('parent-active');
          t.setAttribute('aria-expanded','false');
        } else {
          closeAllExcept(id);
        }
      });
    });

    // ---------- Klik submenu -> set active ----------
    qa('#sidebarMenu .submenu .nav-link').forEach(link=>{
      link.addEventListener('click', function(){
        qa('#sidebarMenu .submenu .nav-link').forEach(l=>l.classList.remove('active'));
        this.classList.add('active');

        qa('.collapse-trigger').forEach(b=>b.classList.remove('parent-active'));
        const parent = this.closest('.collapse');
        if(parent && parent.id){
          const trigger = document.querySelector(`[data-target="#${parent.id}"]`);
          if(trigger) trigger.classList.add('parent-active');
        }

        qa('.dashboard-link').forEach(d=>d.classList.remove('dashboard-active'));
      });
    });

    // ---------- Dashboard click behavior ----------
    const dashLinks = qa('.dashboard-link');
    dashLinks.forEach(dashLink=>{
      dashLink.addEventListener('click', function(e){
        // Jika mau mencegah navigasi (demo) uncomment berikut:
        // e.preventDefault();
        qa('#sidebarMenu .submenu .nav-link').forEach(l=>l.classList.remove('active'));
        qa('.collapse-trigger').forEach(b=>b.classList.remove('parent-active'));
        qa('.dashboard-link').forEach(d=>d.classList.remove('dashboard-active'));
        this.classList.add('dashboard-active');
        closeAllExcept(null);
      });
    });

    // ---------- Pastikan semua submenu tertutup saat load ----------
    triggers.forEach(t=>{
      const id = t.getAttribute('data-target');
      const el = document.querySelector(id);
      if(el){
        safe(()=>bootstrap.Collapse.getOrCreateInstance(el, {toggle:false}).hide());
        t.classList.remove('parent-active');
        t.setAttribute('aria-expanded','false');
      }
    });

    // ---------- Robust URL matching & highlight ----------
    // Ambil currentPath tanpa trailing slash (konsisten)
    const rawPath = (location.pathname || '').replace(/\/+$/, '') || '/';
    const currentPath = rawPath; // ex: '/materi/pengertian-citra'
    const currentLast = currentPath.split('/').filter(Boolean).pop() || '';

    let matched = false;

    qa('#sidebarMenu .submenu .nav-link').forEach(a=>{
      const rawHref = a.getAttribute('href') || '';
      if(!rawHref || rawHref === '#') return;

      // Normalisasi href menjadi pathname (gunakan URL API untuk relative resolution)
      let hrefPath = '/';
      try {
        hrefPath = new URL(rawHref, location.origin).pathname;
      } catch(e){
        // fallback sangat sederhana
        hrefPath = rawHref.split('?')[0].split('#')[0].replace(/^\/+|\/+$/g,'');
        if(!hrefPath.startsWith('/')) hrefPath = '/' + hrefPath;
      }
      hrefPath = hrefPath.replace(/\/+$/, '') || '/';
      const hrefLast = hrefPath.split('/').filter(Boolean).pop() || '';

      // Rules pencocokan (prioritas):
      // 1) exact path match
      // 2) last-segment match (covers '/materi/pengertian-citra' vs '/pengertian-citra')
      // 3) hrefPath is contained inside currentPath (partial)
      if (
        hrefPath === currentPath ||
        (hrefLast !== '' && hrefLast === currentLast) ||
        (hrefPath !== '/' && currentPath.indexOf(hrefPath) !== -1)
      ){
        // tandai active untuk link tersebut
        a.classList.add('active');
        // buka parent collapse dan beri parent-active pada tombol
        const parent = a.closest('.collapse');
        if(parent && parent.id){
          safe(()=>bootstrap.Collapse.getOrCreateInstance(parent, {toggle:false}).show());
          const trigger = document.querySelector(`[data-target="#${parent.id}"]`);
          if(trigger) trigger.classList.add('parent-active');
        }
        matched = true;
      }
    });

    // ---------- Dashboard detection (lengkap) ----------
    // Jika tidak ada submenu yang match, maka putuskan apakah Dashboard harus aktif.
    // Tambahkan path-path custom di sini sesuai route Django Anda.
    const dashboardPaths = [
      '/', '/index', '/index.html',
      '/dash-mhs', '/dash-mhs/', '/dashboard', '/dashboard/',
      '/mhs', '/mhs/', '/mhs/dash-mhs', '/mhs/dash-mhs/'
    ];
    // Normalisasi currentPath tanpa trailing slash
    const currentNoSlash = currentPath === '/' ? '/' : currentPath.replace(/\/+$/, '');

    if(!matched){
      // Jika path ada di daftar dashboardPaths -> set dashboard active
      if(dashboardPaths.indexOf(currentNoSlash) !== -1){
        qa('.dashboard-link').forEach(d=>d.classList.add('dashboard-active'));
        qa('#sidebarMenu .submenu .nav-link').forEach(l=>l.classList.remove('active'));
        qa('.collapse-trigger').forEach(t=>t.classList.remove('parent-active'));
      } else {
        // Jika tidak cocok, hapus highlight dashboard agar tidak tetap aktif
        qa('.dashboard-link').forEach(d=>d.classList.remove('dashboard-active'));
      }
    } else {
      // Jika sudah ada submenu yang match, pastikan dashboard tidak aktif
      qa('.dashboard-link').forEach(d=>d.classList.remove('dashboard-active'));
    }

    // ---------- Small screen: close sidebar ketika klik luar ----------
    document.addEventListener('click', (e)=>{
      if(window.innerWidth <= 992){
        if(sidebar && openBtn && !sidebar.contains(e.target) && !openBtn.contains(e.target)){
          collapsed = true;
          localStorage.setItem('sbCollapsed', true);
          applyState(true);
        }
      }
    });

    // ---------- Optional: expose small helper for debugging ----------
    // window._sidebar_debug = { currentPath, matched };

  })();
});
