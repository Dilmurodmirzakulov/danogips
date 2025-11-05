/* Скрипты для аккордиона */

var acc = document.getElementsByClassName("accordion")
var i

for (i = 0; i < acc.length; i++) {
  acc[i].addEventListener("click", function () {
    this.classList.toggle("active")
    var panel = this.nextElementSibling
    if (panel.style.maxHeight) {
      panel.style.maxHeight = null
    } else {
      panel.style.maxHeight = panel.scrollHeight + "px"
    }
  })
}
try {
  var locate = ymaps.geolocation.city

  if (locate == "Москва") {
    $(".hero-slide.id2557").show()
  }
  if (locate == "Пенза") {
    $(".hero-slide.id2562").show()
  }
  if (locate == "Ростов‑на‑Дону") {
    $(".hero-slide.id2591").show()
  }
  if (locate == "Барнаул") {
    $(".hero-slide.id2602").show()
  }
} catch (error) {

}

// window.onload = function () {
//   var a = document.referrer
//   if (a != '') {
//     console.log(a) // Тут будет полный путь.
//     if (a === "https://www.danogips.ru/") {
//       document.querySelector(".tg-popup").style.display = "flex"
//       document.querySelector(".tg-popup").addEventListener("click", ()=> {
//         document.querySelector(".tg-popup").style.display = "none"
//       })
//     }
//   }
// }