const counterBtn = document.getElementById("counter-btn") as HTMLButtonElement;
const countSpan = document.getElementById("count") as HTMLSpanElement;

let count = 0;

counterBtn.addEventListener("click", () => {
  count++;
  countSpan.textContent = String(count);
});
