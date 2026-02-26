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

    function initGuideSubmenu() {
      var linksContainer = menu.querySelector(".mobile-menu__links");
      if (!linksContainer) {
        return null;
      }

      var existingGroup = linksContainer.querySelector(".mobile-menu__group");
      if (existingGroup) {
        return null;
      }

      var guideLink = linksContainer.querySelector('.mobile-menu__link[href="guide-colors.html"]');
      if (!guideLink) {
        return null;
      }

      var submenuId = menu.id + "-guide-submenu";
      var group = document.createElement("div");
      group.className = "mobile-menu__group";

      var toggle = document.createElement("button");
      toggle.type = "button";
      toggle.className = "mobile-menu__link mobile-menu__link--toggle";
      toggle.setAttribute("aria-expanded", "false");
      toggle.setAttribute("aria-controls", submenuId);
      toggle.innerHTML = '<span>Guide</span><span class="mobile-menu__caret" aria-hidden="true"></span>';

      var submenu = document.createElement("div");
      submenu.className = "mobile-menu__submenu";
      submenu.id = submenuId;
      submenu.hidden = true;

      var currentPage = window.location.pathname.split("/").pop() || "index.html";
      var guidePages = [
        { href: "guide-colors.html", label: "Colors & EMS" },
        { href: "guide-health-priorities.html", label: "Health & Genetics" },
        { href: "guide-daily-care.html", label: "Daily Care" }
      ];

      guidePages.forEach(function (page) {
        var submenuLink = document.createElement("a");
        submenuLink.href = page.href;
        submenuLink.className = "mobile-menu__link mobile-menu__sublink";
        submenuLink.textContent = page.label;
        if (currentPage === page.href) {
          submenuLink.setAttribute("aria-current", "page");
        }
        submenu.appendChild(submenuLink);
      });

      toggle.addEventListener("click", function () {
        var isOpen = toggle.getAttribute("aria-expanded") === "true";
        toggle.setAttribute("aria-expanded", isOpen ? "false" : "true");
        submenu.hidden = isOpen;
      });

      group.appendChild(toggle);
      group.appendChild(submenu);
      linksContainer.replaceChild(group, guideLink);

      return {
        close: function () {
          toggle.setAttribute("aria-expanded", "false");
          submenu.hidden = true;
        }
      };
    }

    var guideSubmenu = initGuideSubmenu();

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
      if (guideSubmenu) {
        guideSubmenu.close();
      }

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
        ? clickTarget.closest(".mobile-menu a[href]")
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

  function initAboutPuzzleGallery() {
    var gallery = document.getElementById("about-puzzle-gallery");
    if (!gallery) {
      return;
    }

    var items = Array.prototype.slice.call(gallery.querySelectorAll(".about-puzzle__item"));
    if (!items.length) {
      return;
    }

    function shuffle(list) {
      var shuffled = list.slice();
      for (var i = shuffled.length - 1; i > 0; i -= 1) {
        var j = Math.floor(Math.random() * (i + 1));
        var temp = shuffled[i];
        shuffled[i] = shuffled[j];
        shuffled[j] = temp;
      }
      return shuffled;
    }

    var randomizedItems = shuffle(items);
    gallery.innerHTML = "";
    randomizedItems.forEach(function (item) {
      gallery.appendChild(item);
    });
  }

  function initFormspreeForms() {
    var forms = document.querySelectorAll('form[action*="formspree.io"]');
    if (!forms.length) {
      return;
    }

    function validatePhoneField(input) {
      if (!input) {
        return true;
      }

      var value = (input.value || "").trim();
      if (!value) {
        input.setCustomValidity("Please enter your phone number.");
        return false;
      }

      var allowedPattern = /^[+0-9().\s-]+$/;
      var digitsCount = value.replace(/\D/g, "").length;
      var isValid = allowedPattern.test(value) && digitsCount >= 8 && digitsCount <= 15;

      if (!isValid) {
        input.setCustomValidity("Please enter a valid phone number (8-15 digits).");
        return false;
      }

      input.setCustomValidity("");
      return true;
    }

    Array.prototype.forEach.call(forms, function (form) {
      if (form.dataset.enhanced === "true") {
        return;
      }
      form.dataset.enhanced = "true";

      var pageInput = document.createElement("input");
      pageInput.type = "hidden";
      pageInput.name = "source_page";
      pageInput.value = window.location.href;
      form.appendChild(pageInput);

      var phoneField = form.querySelector('input[name="phone"]');
      if (phoneField) {
        phoneField.addEventListener("input", function () {
          phoneField.setCustomValidity("");
        });
        phoneField.addEventListener("blur", function () {
          validatePhoneField(phoneField);
        });
      }

      form.addEventListener("submit", function (event) {
        event.preventDefault();

        var submitButton = form.querySelector('button[type="submit"]');
        var defaultButtonText = submitButton ? submitButton.textContent : "";

        if (phoneField && !validatePhoneField(phoneField)) {
          phoneField.reportValidity();
          return;
        }

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

  function buildSharedContactMarkup(instanceId, options) {
    var resolvedOptions = options || {};
    var isCompact = resolvedOptions.isCompact === true;
    var includeTitle = resolvedOptions.includeTitle !== false;
    var contactClass = isCompact ? "about-contact about-contact--compact" : "about-contact";
    var idPrefix = "shared-contact-" + instanceId;
    var nameId = idPrefix + "-name";
    var phoneId = idPrefix + "-phone";
    var emailId = idPrefix + "-email";
    var cityId = idPrefix + "-city";
    var adoptionTypeId = idPrefix + "-adoption-type";
    var timelineId = idPrefix + "-timeline";
    var messageId = idPrefix + "-message";
    var parts = [];

    parts.push('<div class="' + contactClass + '">');
    if (includeTitle) {
      parts.push('<h2>Contact Us</h2>');
    }
    parts.push('<p class="about-contact__intro">Choose the channel you prefer. We usually answer fastest through messaging apps.</p>');
    parts.push('<div class="about-contact__channels" aria-label="Contact options">');
    parts.push('<a href="mailto:wind.in.willows.mc@gmail.com" class="about-channel">');
    parts.push('<span class="about-channel__icon"><img src="public/gmail-4561841_640.png" alt="" loading="lazy" decoding="async" /></span>');
    parts.push('<span>Email</span>');
    parts.push('</a>');
    parts.push('<a href="https://wa.me/33780704461" target="_blank" rel="noreferrer noopener" class="about-channel">');
    parts.push('<span class="about-channel__icon"><img src="public/icons8-whatsapp-48.png" alt="" loading="lazy" decoding="async" /></span>');
    parts.push('<span>WhatsApp</span>');
    parts.push('</a>');
    parts.push('<a href="https://t.me/ekatyousha" target="_blank" rel="noreferrer noopener" class="about-channel">');
    parts.push('<span class="about-channel__icon"><img src="public/Telegram-icon-on-transparent-background-PNG.png" alt="" loading="lazy" decoding="async" /></span>');
    parts.push('<span>Telegram</span>');
    parts.push('</a>');
    parts.push('<a href="https://www.instagram.com/elenachelyadinova/" target="_blank" rel="noreferrer noopener" class="about-channel">');
    parts.push('<span class="about-channel__icon"><img src="public/instagram-6338392_640.png" alt="" loading="lazy" decoding="async" /></span>');
    parts.push('<span>Instagram</span>');
    parts.push('</a>');
    parts.push('<a href="https://www.viber.com/download/" target="_blank" rel="noreferrer noopener" class="about-channel" data-viber-number="+33780704461">');
    parts.push('<span class="about-channel__icon"><img src="public/Viber_logo_2018_(without_text).svg.png" alt="" loading="lazy" decoding="async" /></span>');
    parts.push('<span>Viber</span>');
    parts.push('</a>');
    parts.push('<a href="https://www.facebook.com/profile.php?id=61557493987171" target="_blank" rel="noreferrer noopener" class="about-channel">');
    parts.push('<span class="about-channel__icon"><img src="public/icons8-facebook-48.png" alt="" loading="lazy" decoding="async" /></span>');
    parts.push('<span>Messenger</span>');
    parts.push('</a>');
    parts.push('</div>');
    parts.push('<p class="about-contact__copy-email">For email inquiries, please contact:<span class="about-contact__email-value">wind.in.willows.mc@gmail.com</span><span class="about-contact__email-hint">Tap to copy</span></p>');
    parts.push('<h3 class="about-contact__form-title">Prefer a detailed request? Send the form below.</h3>');
    parts.push('<form id="' + idPrefix + '-form" class="form about-contact__form" action="https://formspree.io/f/xovqlvod" method="POST">');
    parts.push('<input type="hidden" name="_next" value="https://www.wind-in-willows.com/thank-you.html" />');
    parts.push('<div class="form__group">');
    parts.push('<label class="form__label" for="' + nameId + '">Your name</label>');
    parts.push('<input type="text" id="' + nameId + '" name="name" required class="form__input" placeholder="Enter your name" />');
    parts.push('</div>');
    parts.push('<div class="form__group">');
    parts.push('<label class="form__label" for="' + phoneId + '">Phone number</label>');
    parts.push('<input type="tel" id="' + phoneId + '" name="phone" required inputmode="tel" autocomplete="tel" class="form__input" placeholder="Enter your phone number" />');
    parts.push('</div>');
    parts.push('<div class="form__group">');
    parts.push('<label class="form__label" for="' + emailId + '">Email address</label>');
    parts.push('<input type="email" id="' + emailId + '" name="email" required autocomplete="email" class="form__input" placeholder="Enter your email" />');
    parts.push('</div>');
    parts.push('<div class="form__group">');
    parts.push('<label class="form__label" for="' + cityId + '">City</label>');
    parts.push('<input type="text" id="' + cityId + '" name="city" required class="form__input" placeholder="Enter your city" />');
    parts.push('</div>');
    parts.push('<div class="form__group">');
    parts.push('<label class="form__label" for="' + adoptionTypeId + '">Adoption type</label>');
    parts.push('<select id="' + adoptionTypeId + '" name="adoption_type" class="form__select">');
    parts.push('<option value="">Select type</option>');
    parts.push('<option value="Pet">Pet</option>');
    parts.push('<option value="Breed">Breed</option>');
    parts.push('<option value="Other">Other</option>');
    parts.push('</select>');
    parts.push('</div>');
    parts.push('<div class="form__group">');
    parts.push('<label class="form__label" for="' + timelineId + '">When are you planning to bring a kitten home?</label>');
    parts.push('<select id="' + timelineId + '" name="purchase_timeline" required class="form__select">');
    parts.push('<option value="">Select your timeline</option>');
    parts.push('<option value="Ready soon (next 2-4 weeks)">Ready soon (next 2-4 weeks)</option>');
    parts.push('<option value="Planning for the next few months">Planning for the next few months</option>');
    parts.push('<option value="Just exploring options">Just exploring options for now</option>');
    parts.push('</select>');
    parts.push('</div>');
    parts.push('<div class="form__group">');
    parts.push('<label class="form__label" for="' + messageId + '">Your message (please include details)</label>');
    parts.push('<textarea id="' + messageId + '" name="message" required class="form__textarea" placeholder="Share your kitten preferences, desired colors, household details, and any questions."></textarea>');
    parts.push('</div>');
    parts.push('<button type="submit" class="btn btn--primary">Send Message</button>');
    parts.push('</form>');
    parts.push('</div>');

    return parts.join("");
  }

  function initSharedContactSections() {
    var mountPoints = document.querySelectorAll("[data-shared-contact-section]");
    if (!mountPoints.length) {
      return;
    }

    Array.prototype.forEach.call(mountPoints, function (mountPoint, index) {
      var variant = (mountPoint.getAttribute("data-shared-contact-section") || "").toLowerCase();
      var options = {
        isCompact: false,
        includeTitle: true
      };

      if (variant === "compact") {
        options.isCompact = true;
      } else if (variant === "compact-no-title" || variant === "home") {
        options.isCompact = true;
        options.includeTitle = false;
      }

      mountPoint.innerHTML = buildSharedContactMarkup(index + 1, options);
    });
  }

  function initViberLinks() {
    var viberLinks = document.querySelectorAll("a[data-viber-number]");
    if (!viberLinks.length) {
      return;
    }

    Array.prototype.forEach.call(viberLinks, function (link) {
      link.addEventListener("click", function (event) {
        var rawNumber = link.getAttribute("data-viber-number") || "";
        var normalizedNumber = rawNumber.replace(/\s+/g, "");
        if (!normalizedNumber) {
          return;
        }

        var fallbackUrl = link.getAttribute("href") || "https://www.viber.com/download/";
        var deepLinkUrl = "viber://chat/?number=" + encodeURIComponent(normalizedNumber);
        var didHide = false;

        function handleVisibilityChange() {
          if (document.hidden) {
            didHide = true;
            cleanup();
          }
        }

        function cleanup() {
          clearTimeout(fallbackTimer);
          document.removeEventListener("visibilitychange", handleVisibilityChange);
        }

        event.preventDefault();
        document.addEventListener("visibilitychange", handleVisibilityChange);

        var fallbackTimer = setTimeout(function () {
          cleanup();
          if (!didHide) {
            window.open(fallbackUrl, "_blank", "noopener,noreferrer");
          }
        }, 1100);

        window.location.href = deepLinkUrl;
      });
    });
  }

  function init() {
    initMobileMenu();
    initFaqAccordions();
    initAboutPuzzleGallery();
    initSharedContactSections();
    initFormspreeForms();
    initViberLinks();
    initCtaTracking();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
