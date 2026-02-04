document.addEventListener('DOMContentLoaded', function () {
    (function () {
        const sidebar = document.getElementById('sidebar');
        const main = document.getElementById('main');
        const sidebarToggle = document.getElementById('sidebarToggle');
        const sidebarToggleIcon = document.getElementById('sidebarToggleIcon');
        const openBtn = document.getElementById('openBtn');

        const q = (sel) => document.querySelector(sel);
        const qa = (sel) => Array.from(document.querySelectorAll(sel));
        const safe = (fn) => { try { return fn(); } catch (e) { return null; } };

        let collapsed = localStorage.getItem('sbCollapsed') === 'true';

        function applyState(isCollapsed) {
            if (!sidebar || !main) return;
            if (isCollapsed) {
                sidebar.classList.add('collapsed');
                main.classList.add('full');
                if (openBtn) openBtn.classList.add('visible');
                if (sidebarToggleIcon) sidebarToggleIcon.className = 'bi bi-chevron-right';
            } else {
                sidebar.classList.remove('collapsed');
                main.classList.remove('full');
                if (openBtn) openBtn.classList.remove('visible');
                if (sidebarToggleIcon) sidebarToggleIcon.className = 'bi bi-chevron-left';
            }
        }

        applyState(collapsed);

        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', () => {
                collapsed = true;
                localStorage.setItem('sbCollapsed', true);
                applyState(true);
            });
        }

        if (openBtn) {
            openBtn.addEventListener('click', () => {
                collapsed = false;
                localStorage.setItem('sbCollapsed', false);
                applyState(false);
            });
        }

        const triggers = qa('.collapse-trigger');

        function closeAllExcept(openId) {
            triggers.forEach(t => {
                const target = t.getAttribute('data-target');
                const el = document.querySelector(target);
                if (!el) return;
                if (target !== openId) {
                    safe(() => bootstrap.Collapse.getOrCreateInstance(el).hide());
                    t.classList.remove('parent-active');
                    t.setAttribute('aria-expanded', 'false');
                } else {
                    safe(() => bootstrap.Collapse.getOrCreateInstance(el).show());
                    t.classList.add('parent-active');
                    t.setAttribute('aria-expanded', 'true');
                }
            });
        }

        triggers.forEach(t => {
            t.addEventListener('click', function (e) {
                e.preventDefault();
                const id = t.getAttribute('data-target');
                const el = document.querySelector(id);
                if (!el) return;
                if (el.classList.contains('show')) {
                    safe(() => bootstrap.Collapse.getOrCreateInstance(el).hide());
                    t.classList.remove('parent-active');
                    t.setAttribute('aria-expanded', 'false');
                } else {
                    closeAllExcept(id);
                }
            });
        });

        const subLinks = qa('#sidebarMenu .submenu .nav-link');
        subLinks.forEach(link => {
            link.addEventListener('click', function () {
                subLinks.forEach(l => l.classList.remove('active'));
                this.classList.add('active');
                qa('.collapse-trigger').forEach(b => b.classList.remove('parent-active'));
                const parent = this.closest('.collapse');
                if (parent && parent.id) {
                    const trigger = document.querySelector(`[data-target="#${parent.id}"]`);
                    if (trigger) trigger.classList.add('parent-active');
                }
                qa('.dashboard-link').forEach(d => d.classList.remove('dashboard-active'));
            });
        });

        const dashLinks = qa('.dashboard-link');
        dashLinks.forEach(dashLink => {
            dashLink.addEventListener('click', function () {
                subLinks.forEach(l => l.classList.remove('active'));
                qa('.collapse-trigger').forEach(b => b.classList.remove('parent-active'));
                dashLinks.forEach(d => d.classList.remove('dashboard-active'));
                this.classList.add('dashboard-active');
                closeAllExcept(null);
            });
        });

        triggers.forEach(t => {
            const id = t.getAttribute('data-target');
            const el = document.querySelector(id);
            if (el) {
                safe(() => bootstrap.Collapse.getOrCreateInstance(el, { toggle: false }).hide());
                t.classList.remove('parent-active');
                t.setAttribute('aria-expanded', 'false');
            }
        });

        const currentPath = (location.pathname || '').replace(/\/+$/, '') || '/';
        const currentLast = currentPath.split('/').filter(Boolean).pop() || '';
        let matched = false;

        subLinks.forEach(a => {
            const rawHref = a.getAttribute('href') || '';
            if (!rawHref || rawHref === '#') return;

            let hrefPath = '/';
            try {
                hrefPath = new URL(rawHref, location.origin).pathname;
            } catch (e) {
                hrefPath = rawHref.split('?')[0].split('#')[0].replace(/^\/+|\/+$/g, '');
                if (!hrefPath.startsWith('/')) hrefPath = '/' + hrefPath;
            }
            hrefPath = hrefPath.replace(/\/+$/, '') || '/';
            const hrefLast = hrefPath.split('/').filter(Boolean).pop() || '';

            if (hrefPath === currentPath || (hrefLast !== '' && hrefLast === currentLast) || (hrefPath !== '/' && currentPath.indexOf(hrefPath) !== -1)) {
                a.classList.add('active');
                const parent = a.closest('.collapse');
                if (parent && parent.id) {
                    safe(() => bootstrap.Collapse.getOrCreateInstance(parent, { toggle: false }).show());
                    const trigger = document.querySelector(`[data-target="#${parent.id}"]`);
                    if (trigger) trigger.classList.add('parent-active');
                }
                matched = true;
            }
        });

        const dashboardPaths = ['/', '/index', '/index.html', '/dash-mhs', '/dash-mhs/', '/dashboard', '/dashboard/', '/mhs', '/mhs/', '/mhs/dash-mhs', '/mhs/dash-mhs/'];
        const currentNoSlash = currentPath === '/' ? '/' : currentPath.replace(/\/+$/, '');

        if (!matched) {
            if (dashboardPaths.indexOf(currentNoSlash) !== -1) {
                dashLinks.forEach(d => d.classList.add('dashboard-active'));
                subLinks.forEach(l => l.classList.remove('active'));
                qa('.collapse-trigger').forEach(t => t.classList.remove('parent-active'));
            } else {
                dashLinks.forEach(d => d.classList.remove('dashboard-active'));
            }
        } else {
            dashLinks.forEach(d => d.classList.remove('dashboard-active'));
        }

        document.addEventListener('click', (e) => {
            if (window.innerWidth <= 992) {
                if (sidebar && openBtn && !sidebar.contains(e.target) && !openBtn.contains(e.target)) {
                    collapsed = true;
                    localStorage.setItem('sbCollapsed', true);
                    applyState(true);
                }
            }
        });
    })();
});