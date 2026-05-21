// Reusable Roller Loader
function startRoller(button) {
  if (!button.classList.contains('btn-roller')) return;
  button.classList.add('loading');
  button.disabled = true;
}

function stopRoller(button) {
  if (!button.classList.contains('btn-roller')) return;
  button.classList.remove('loading');
  button.disabled = false;
}

// Optional: Auto stop after a delay (for demo/testing)
function simulateRoller(button, delay = 2000) {
  startRoller(button);
  setTimeout(() => stopRoller(button), delay);
}
