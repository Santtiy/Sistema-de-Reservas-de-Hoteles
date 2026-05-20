document.addEventListener("click", (event) => {
	const menu = document.querySelector("[data-mobile-menu]");
	if (!menu) {
		return;
	}

	const toggle = event.target.closest("[data-menu-toggle]");
	const close = event.target.closest("[data-menu-close]");

	if (toggle) {
		menu.classList.add("open");
		return;
	}

	if (close || event.target === menu) {
		menu.classList.remove("open");
	}
});
