document.addEventListener('DOMContentLoaded', function () {
    (function () {
        const sidebar = document.getElementById('sidebar');
        const main = document.getElementById('main');
        const sidebarToggle = document.getElementById('sidebarToggle');
        const sidebarToggleIcon = document.getElementById('sidebarToggleIcon');
        const openBtn = document.getElementById('openBtn');

        const q = (sel) => document.querySelector(sel);
        const qa = (sel) => Array.from(document.querySelectorAll(sel));

        let collapsed = localStorage.getItem('sbCollapsed') === 'true';
        applyState(collapsed);

        function applyState(isCollapsed) {
            if (isCollapsed) {
                sidebar.classList.add('collapsed');
                main.classList.add('full');
                openBtn.classList.add('visible');
                if (sidebarToggleIcon) sidebarToggleIcon.className = 'bi bi-chevron-right';
            } else {
                sidebar.classList.remove('collapsed');
                main.classList.remove('full');
                openBtn.classList.remove('visible');
                if (sidebarToggleIcon) sidebarToggleIcon.className = 'bi bi-chevron-left';
            }
        }

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

        function closeAllExcept(id) {
            triggers.forEach(t => {
                const target = t.getAttribute('data-target');
                const el = q(target);
                if (!el) return;

                const collapseInstance = bootstrap.Collapse.getOrCreateInstance(el);
                if (target !== id) {
                    collapseInstance.hide();
                    t.classList.remove('parent-active');
                    t.setAttribute('aria-expanded', 'false');
                } else {
                    collapseInstance.show();
                    t.classList.add('parent-active');
                    t.setAttribute('aria-expanded', 'true');
                }
            });
        }

        triggers.forEach(t => {
            t.addEventListener('click', function (e) {
                e.preventDefault();
                const id = t.getAttribute('data-target');
                const el = q(id);
                if (!el) return;

                if (el.classList.contains('show')) {
                    bootstrap.Collapse.getOrCreateInstance(el).hide();
                    t.classList.remove('parent-active');
                    t.setAttribute('aria-expanded', 'false');
                } else {
                    closeAllExcept(id);
                }
            });
        });

        const navLinks = qa('#sidebarMenu .submenu .nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', function () {
                navLinks.forEach(l => l.classList.remove('active'));
                this.classList.add('active');

                qa('.collapse-trigger').forEach(b => b.classList.remove('parent-active'));
                const parent = this.closest('.collapse');
                if (parent && parent.id) {
                    const trigger = q(`[data-target="#${parent.id}"]`);
                    if (trigger) trigger.classList.add('parent-active');
                }

                qa('.dashboard-link').forEach(d => d.classList.remove('dashboard-active'));
            });
        });

        const currentPath = location.pathname.replace(/\/+$/, '') || '/';
        const currentLast = currentPath.split('/').filter(Boolean).pop() || '';
        let matched = false;

        qa('#sidebarMenu .submenu .nav-link').forEach(a => {
            const href = a.getAttribute('href');
            if (!href || href === '#') return;

            let hrefPath;
            try {
                hrefPath = new URL(href, location.origin).pathname;
            } catch {
                hrefPath = href.replace(/^\/+|\/+$/g, '');
                if (!hrefPath.startsWith('/')) hrefPath = '/' + hrefPath;
            }
            hrefPath = hrefPath.replace(/\/+$/, '') || '/';
            const hrefLast = hrefPath.split('/').filter(Boolean).pop() || '';

            if (hrefPath === currentPath || hrefLast === currentLast || (currentPath.includes(hrefPath) && hrefPath !== '/')) {
                a.classList.add('active');
                const parent = a.closest('.collapse');
                if (parent && parent.id) {
                    bootstrap.Collapse.getOrCreateInstance(parent, { toggle: false }).show();
                    const trigger = q(`[data-target="#${parent.id}"]`);
                    if (trigger) trigger.classList.add('parent-active');
                }
                matched = true;
            }
        });

        if (!matched) {
            const last = currentPath.split('/').filter(Boolean).pop() || '';
            if (currentPath === '/' || last === 'index') {
                qa('.dashboard-link').forEach(d => d.classList.add('dashboard-active'));
            } else {
                qa('.dashboard-link').forEach(d => d.classList.remove('dashboard-active'));
            }
        } else {
            qa('.dashboard-link').forEach(d => d.classList.remove('dashboard-active'));
        }

        document.addEventListener('click', (e) => {
            if (window.innerWidth <= 992) {
                if (sidebar && !sidebar.contains(e.target) && openBtn && !openBtn.contains(e.target)) {
                    collapsed = true;
                    localStorage.setItem('sbCollapsed', true);
                    applyState(true);
                }
            }
        });
    })();
});