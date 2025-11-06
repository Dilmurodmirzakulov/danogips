$(document).ready(function(){
var swiper = new Swiper(".hero-slider", {
    slidesPerView: 1,
    spaceBetween: 0,
    pagination: {
        el: ".swiper-pagination",
      },
    navigation: {
      nextEl: ".hero-next",
      prevEl: ".hero-prev",
    },
  });
});