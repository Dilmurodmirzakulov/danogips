/**
 * Danogips Dynamic Content Widget
 *
 * Replaces static banner slides with dynamic ones from the admin API.
 * Works with the existing Swiper.js slider on the Danogips site.
 *
 * Usage:
 *   Place <script src="/widgets/danogips-widget.js"></script> after the
 *   Swiper init script (design2023/js/slider.js) in both index.html and uz/index.html.
 *
 * Configuration (optional):
 *   window.DANOGIPS_WIDGET = { apiBase: "https://api.uzchem.uz" };
 */
(function () {
  "use strict";

  /* ── Config ────────────────────────────────── */
  var cfg = window.DANOGIPS_WIDGET || {};
  var API = cfg.apiBase || "";
  var lang =
    window.location.pathname.indexOf("/uz") === 0 ||
    window.location.pathname.indexOf("/uz/") !== -1
      ? "uz"
      : "ru";

  function lk(prefix) {
    return prefix + "_" + lang;
  }

  /* ── Helpers ───────────────────────────────── */
  function fetchJSON(url) {
    return fetch(API + url)
      .then(function (res) {
        if (!res.ok) return null;
        return res.json();
      })
      .catch(function () {
        return null;
      });
  }

  /* ── Banners ───────────────────────────────── */
  function renderBanners() {
    var wrapper = document.querySelector(".hero-wrapper.swiper-wrapper");
    if (!wrapper) return;

    fetchJSON("/api/danogips/banners?active=true").then(function (resp) {
      var data = resp && resp.data ? resp.data : resp;
      if (!data || !data.length) return;

      /* Remove old static slides */
      wrapper.innerHTML = "";

      /* Build dynamic slides */
      data.forEach(function (b) {
        var slide = document.createElement("div");
        slide.className = "hero-slide swiper-slide";

        var title = b[lk("title")] || b.title_ru || b.title_uz || "";
        var link = b.link || "";
        var imgSrc = b.image || "";

        /* Resolve image URL:
           - absolute URL (http/https) → use as-is
           - /uploads/... → prefix with API base (admin-uploaded files)
           - anything else → make root-absolute so both /ru and /uz pages
             load from the same site root (e.g. "img/slider/x.jpg" → "/img/slider/x.jpg") */
        if (imgSrc && imgSrc.indexOf("http") !== 0) {
          if (imgSrc.indexOf("/uploads") === 0) {
            imgSrc = API + imgSrc;
          } else if (imgSrc.indexOf("/") !== 0) {
            /* site-relative path — prepend "/" to make it root-absolute */
            imgSrc = "/" + imgSrc;
          }
          /* paths already starting with "/" are used as-is */
        }

        var img = document.createElement("img");
        img.className = "hero-img";
        img.alt = title;
        img.src = imgSrc;

        if (link) {
          var a = document.createElement("a");
          a.href = link;
          a.appendChild(img);
          slide.appendChild(a);
        } else {
          slide.appendChild(img);
        }

        wrapper.appendChild(slide);
      });

      /* Re-initialize Swiper if it exists, so it picks up new slides */
      reinitSwiper();
    });
  }

  function reinitSwiper() {
    var container = document.querySelector(".hero-slider.swiper");
    if (!container) return;

    /* If Swiper instance exists on the element, destroy & rebuild */
    if (container.swiper) {
      container.swiper.destroy(true, true);
    }

    /* Small delay to let DOM settle */
    setTimeout(function () {
      if (typeof Swiper !== "undefined") {
        new Swiper(".hero-slider", {
          loop: true,
          autoplay: {
            delay: 5000,
            disableOnInteraction: false,
          },
          pagination: {
            el: ".swiper-pagination",
            clickable: true,
          },
          navigation: {
            nextEl: ".hero-next",
            prevEl: ".hero-prev",
          },
        });
      }
    }, 100);
  }

  /* ── Init ───────────────────────────────────── */
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", renderBanners);
  } else {
    renderBanners();
  }
})();
