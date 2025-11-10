document.addEventListener("DOMContentLoaded", function () {
  // Smooth fade-in for table and header
  const header = document.querySelector("h2");
  const table = document.querySelector("table");
  header.style.opacity = "0";
  table.style.opacity = "0";
  header.style.transform = "translateY(-10px)";
  table.style.transform = "translateY(20px)";

  setTimeout(() => {
    header.style.transition = "all 0.8s ease";
    table.style.transition = "all 0.8s ease";
    header.style.opacity = "1";
    header.style.transform = "translateY(0)";
    table.style.opacity = "1";
    table.style.transform = "translateY(0)";
  }, 200);

  // Button click ripple effect
  document.querySelectorAll("button").forEach(btn => {
    btn.addEventListener("click", function (e) {
      const circle = document.createElement("span");
      circle.classList.add("ripple");
      this.appendChild(circle);

      const diameter = Math.max(this.clientWidth, this.clientHeight);
      const rect = this.getBoundingClientRect();
      circle.style.width = circle.style.height = `${diameter}px`;
      circle.style.left = `${e.clientX - rect.left - diameter / 2}px`;
      circle.style.top = `${e.clientY - rect.top - diameter / 2}px`;

      setTimeout(() => circle.remove(), 600);
    });
  });

  // Smooth scroll to top on adding or editing
  const form = document.querySelector("form");
  form.addEventListener("submit", () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  });

  // Flash message animation (fade-out after 3s)
  const msg = document.querySelector("p");
  if (msg) {
    setTimeout(() => {
      msg.style.transition = "opacity 1s";
      msg.style.opacity = "0";
    }, 3000);
  }
});

// Ripple Effect Styling (auto-injected)
const rippleStyle = document.createElement("style");
rippleStyle.innerHTML = `
  .ripple {
    position: absolute;
    border-radius: 50%;
    transform: scale(0);
    animation: ripple 0.6s linear;
    background-color: rgba(255, 255, 255, 0.7);
    pointer-events: none;
  }
  @keyframes ripple {
    to {
      transform: scale(4);
      opacity: 0;
    }
  }
  button {
    position: relative;
    overflow: hidden;
  }
`;
document.head.appendChild(rippleStyle);
