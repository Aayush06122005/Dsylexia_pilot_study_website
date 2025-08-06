function scrollToSection(id) {
  document.getElementById(id).scrollIntoView({ behavior: "smooth" });
}



// Optional: trigger fade-ins on scroll
window.addEventListener("scroll", () => {
  document.querySelectorAll(".fade-in").forEach(el => {
    const rect = el.getBoundingClientRect();
    if (rect.top < window.innerHeight - 100) {
      el.style.animationPlayState = "running";
    }
  });
});
