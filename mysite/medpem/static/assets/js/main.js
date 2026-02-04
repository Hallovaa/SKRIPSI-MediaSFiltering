(function () {
    window.onload = function () {
        window.setTimeout(fadeout, 300);
    };

    function fadeout() {
        const preloader = document.querySelector('.preloader');
        if (preloader) {
            preloader.style.opacity = '0';
            preloader.style.display = 'none';
        }
    }

    window.onscroll = function () {
        const header_navbar = document.querySelector(".hero-section-wrapper-5 .header");
        const backToTo = document.querySelector(".scroll-top");

        if (header_navbar) {
            const sticky = header_navbar.offsetTop;
            if (window.pageYOffset > sticky) {
                header_navbar.classList.add("sticky");
            } else {
                header_navbar.classList.remove("sticky");
            }
        }

        if (backToTo) {
            if (document.body.scrollTop > 50 || document.documentElement.scrollTop > 50) {
                backToTo.style.display = "flex";
            } else {
                backToTo.style.display = "none";
            }
        }
    };

    const navbarToggler6 = document.querySelector(".header-6 .navbar-toggler");
    const navbarCollapse6 = document.querySelector(".header-6 .navbar-collapse");

    if (navbarToggler6 && navbarCollapse6) {
        document.querySelectorAll(".header-6 .page-scroll").forEach(e =>
            e.addEventListener("click", () => {
                navbarToggler6.classList.remove("active");
                navbarCollapse6.classList.remove('show');
            })
        );

        navbarToggler6.addEventListener('click', function () {
            navbarToggler6.classList.toggle("active");
        });
    }

    function onScroll(event) {
        const sections = document.querySelectorAll('.page-scroll');
        const scrollPos = window.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop;

        for (let i = 0; i < sections.length; i++) {
            const currLink = sections[i];
            const val = currLink.getAttribute('href');
            
            if (val.startsWith('#')) {
                const refElement = document.querySelector(val);
                if (refElement) {
                    const scrollTopMinus = scrollPos + 73;
                    if (refElement.offsetTop <= scrollTopMinus && (refElement.offsetTop + refElement.offsetHeight > scrollTopMinus)) {
                        document.querySelectorAll('.page-scroll').forEach(link => link.classList.remove('active'));
                        currLink.classList.add('active');
                    } else {
                        currLink.classList.remove('active');
                    }
                }
            }
        }
    }

    window.document.addEventListener('scroll', onScroll);

    const pricingContainer = document.querySelector('.pricing-active');
    if (pricingContainer) {
        tns({
            container: '.pricing-active',
            autoplay: false,
            mouseDrag: true,
            gutter: 0,
            nav: false,
            controls: true,
            controlsText: [
                '<i class="lni lni-chevron-left prev"></i>',
                '<i class="lni lni-chevron-right prev"></i>',
            ],
            responsive: {
                0: { items: 1 },
                768: { items: 2 },
                992: { items: 1.2 },
                1200: { items: 2 }
            }
        });
    }

    if (typeof WOW !== 'undefined') {
        new WOW().init();
    }
})();