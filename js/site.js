"use strict";

(function () {
  function trackEvent(name, params) {
    if (typeof window.gtag === "function") {
      window.gtag("event", name, params || {});
    }
  }

  function initCtaTracking() {
    document.addEventListener("click", function (event) {
      var clickTarget = event.target.nodeType === 1 ? event.target : event.target.parentElement;
      var target = clickTarget && typeof clickTarget.closest === "function"
        ? clickTarget.closest("a.btn, button.btn")
        : null;
      if (!target) {
        return;
      }

      trackEvent("cta_click", {
        cta_text: (target.textContent || "").trim().slice(0, 80),
        cta_href: target.getAttribute("href") || "",
        page_path: window.location.pathname
      });
    });
  }

  function initMobileMenu() {
    var menu = document.querySelector(".mobile-menu");
    var openButton = document.querySelector(".navbar__burger");
    var closeButton = document.querySelector(".mobile-menu__close");

    if (!menu || !openButton || !closeButton) {
      return;
    }

    var previousFocus = null;
    var focusableSelector = 'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])';

    if (!menu.id) {
      menu.id = "mobile-navigation";
    }

    openButton.setAttribute("aria-controls", menu.id);
    openButton.setAttribute("aria-expanded", "false");
    menu.setAttribute("aria-hidden", "true");

    function getFocusable() {
      return Array.prototype.slice.call(menu.querySelectorAll(focusableSelector)).filter(function (el) {
        return el.offsetParent !== null;
      });
    }

    function closeMenu() {
      if (!menu.classList.contains("active")) {
        return;
      }

      menu.classList.remove("active");
      menu.setAttribute("aria-hidden", "true");
      openButton.setAttribute("aria-expanded", "false");
      document.body.style.overflow = "";

      if (previousFocus && typeof previousFocus.focus === "function") {
        previousFocus.focus();
      }
    }

    function openMenu() {
      previousFocus = document.activeElement;
      menu.classList.add("active");
      menu.setAttribute("aria-hidden", "false");
      openButton.setAttribute("aria-expanded", "true");
      document.body.style.overflow = "hidden";

      var focusable = getFocusable();
      if (focusable.length) {
        focusable[0].focus();
      } else {
        closeButton.focus();
      }
    }

    function trapFocus(event) {
      if (!menu.classList.contains("active") || event.key !== "Tab") {
        return;
      }

      var focusable = getFocusable();
      if (!focusable.length) {
        event.preventDefault();
        return;
      }

      var first = focusable[0];
      var last = focusable[focusable.length - 1];

      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }

    openButton.addEventListener("click", openMenu);
    closeButton.addEventListener("click", closeMenu);

    menu.addEventListener("click", function (event) {
      var clickTarget = event.target.nodeType === 1 ? event.target : event.target.parentElement;
      var linkTarget = clickTarget && typeof clickTarget.closest === "function"
        ? clickTarget.closest(".mobile-menu__link")
        : null;
      if (linkTarget) {
        closeMenu();
      }
    });

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") {
        closeMenu();
      }
      trapFocus(event);
    });
  }

  function setFaqState(item, isOpen) {
    var question = item.querySelector(".faq__question");
    var answer = item.querySelector(".faq__answer");

    if (!question || !answer) {
      return;
    }

    item.classList.toggle("active", isOpen);
    question.setAttribute("aria-expanded", isOpen ? "true" : "false");
    answer.hidden = !isOpen;
  }

  function initFaqAccordions() {
    var items = document.querySelectorAll(".faq__item");
    if (!items.length) {
      return;
    }

    Array.prototype.forEach.call(items, function (item, index) {
      var question = item.querySelector(".faq__question");
      var answer = item.querySelector(".faq__answer");

      if (!question || !answer) {
        return;
      }

      var answerId = answer.id || "faq-answer-" + (index + 1);
      answer.id = answerId;
      question.setAttribute("aria-controls", answerId);

      if (question.tagName !== "BUTTON") {
        question.setAttribute("role", "button");
        question.setAttribute("tabindex", "0");
      }

      setFaqState(item, item.classList.contains("active"));

      question.addEventListener("click", function () {
        var open = !item.classList.contains("active");
        Array.prototype.forEach.call(items, function (entry) {
          setFaqState(entry, false);
        });
        setFaqState(item, open);
      });

      question.addEventListener("keydown", function (event) {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          question.click();
        }
      });
    });
  }

  function initFormspreeForms() {
    var forms = document.querySelectorAll('form[action*="formspree.io"]');
    if (!forms.length) {
      return;
    }

    Array.prototype.forEach.call(forms, function (form) {
      if (form.dataset.enhanced === "true") {
        return;
      }
      form.dataset.enhanced = "true";

      form.addEventListener("submit", function (event) {
        event.preventDefault();

        var submitButton = form.querySelector('button[type="submit"]');
        var defaultButtonText = submitButton ? submitButton.textContent : "";

        if (submitButton) {
          submitButton.disabled = true;
          submitButton.textContent = "Sending...";
        }

        fetch(form.action, {
          method: "POST",
          body: new FormData(form),
          headers: { Accept: "application/json" }
        }).then(function (response) {
          if (response.ok) {
            var conversionPayload = {
              form_id: form.id || "contact-form",
              page_path: window.location.pathname
            };
            trackEvent("form_submit_success", conversionPayload);
            trackEvent("generate_lead", conversionPayload);
            setTimeout(function () {
              window.location.href = "thank-you.html";
            }, 120);
            return;
          }

          return response.json().then(function (data) {
            var fallbackMessage = "Unable to send your message. Please try again.";
            var apiMessage = data && data.errors && data.errors[0] && data.errors[0].message;
            throw new Error(apiMessage || fallbackMessage);
          }).catch(function () {
            throw new Error("Unable to send your message. Please try again.");
          });
        }).catch(function (error) {
          alert(error.message || "Unable to send your message. Please try again.");
        }).finally(function () {
          if (submitButton) {
            submitButton.disabled = false;
            submitButton.textContent = defaultButtonText;
          }
        });
      });
    });
  }

  function init() {
    initMobileMenu();
    initFaqAccordions();
    initFormspreeForms();
    initCtaTracking();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
