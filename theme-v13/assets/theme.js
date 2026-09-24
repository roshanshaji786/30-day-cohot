/* ==========================================================================
   Cohort theme — interactions. No dependencies, no polyfills, ~9 KB unmin.
   Everything degrades gracefully: without JS the markup still works
   (real <form> elements, real <a href> links, native <details> accordions).
   ========================================================================== */
(function () {
  'use strict';

  var root = window.Shopify && window.Shopify.routes && window.Shopify.routes.root
    ? window.Shopify.routes.root
    : '/';
  var $ = function (sel, ctx) { return (ctx || document).querySelector(sel); };
  var $$ = function (sel, ctx) { return Array.prototype.slice.call((ctx || document).querySelectorAll(sel)); };
  var moneyFormat = (window.themeStrings && window.themeStrings.moneyFormat) || null;

  function announce(message) {
    var live = document.getElementById('a11y-status');
    if (live) { live.textContent = message; }
  }

  function formatMoney(cents) {
    if (typeof cents !== 'number') { return ''; }
    if (!moneyFormat) { return (cents / 100).toFixed(2); }
    return moneyFormat.replace(/\{\{\s*(\w+)\s*\}\}/, function (m, key) {
      var value = (cents / 100).toFixed(2);
      var sep = value.replace(/\B(?=(\d{3})+(?!\d))/g, ',');
      if (key === 'amount') { return value; }
      if (key === 'amount_no_decimals') { return Math.round(cents / 100); }
      if (key === 'amount_with_comma_separator') { return sep; }
      if (key === 'amount_no_decimals_with_comma_separator') { return value.split('.')[0].replace(/\B(?=(\d{3})+(?!\d))/g, ','); }
      return sep;
    });
  }

  /* ------------------------------------------------------------ header */
  var header = $('[data-header]');
  if (header) {
    var onScroll = function () {
      if (window.scrollY > 12) { header.classList.add('is-scrolled'); }
      else { header.classList.remove('is-scrolled'); }
    };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  /* -------------------------------------------------------- mobile menu */
  var menuDialog = $('[data-mobile-menu]');
  var menuToggle = $('[data-nav-toggle]');
  if (menuDialog && menuToggle) {
    var openMenu = function () {
      if (typeof menuDialog.showModal === 'function') { menuDialog.showModal(); }
      else { menuDialog.setAttribute('open', ''); }
      menuToggle.setAttribute('aria-expanded', 'true');
      document.documentElement.style.overflow = 'hidden';
      var first = $('.mobile-menu__link', menuDialog);
      if (first) { first.focus(); }
    };
    var closeMenu = function () {
      if (typeof menuDialog.close === 'function' && menuDialog.open) { menuDialog.close(); }
      else { menuDialog.removeAttribute('open'); }
      menuToggle.setAttribute('aria-expanded', 'false');
      document.documentElement.style.overflow = '';
      menuToggle.focus();
    };
    menuToggle.addEventListener('click', function () {
      if (menuDialog.open) { closeMenu(); } else { openMenu(); }
    });
    $$('[data-nav-close]', menuDialog).forEach(function (btn) { btn.addEventListener('click', closeMenu); });
    menuDialog.addEventListener('click', function (event) {
      if (event.target === menuDialog) { closeMenu(); }
    });
    menuDialog.addEventListener('close', function () {
      menuToggle.setAttribute('aria-expanded', 'false');
      document.documentElement.style.overflow = '';
    });
  }

  /* ------------------------------------------------------- nav dropdowns */
  $$('.site-nav__link--toggle').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var expanded = btn.getAttribute('aria-expanded') === 'true';
      btn.setAttribute('aria-expanded', expanded ? 'false' : 'true');
    });
  });

  /* ----------------------------------------------------------- countdown */
  var CountdownTimer = function (el) {
    this.el = el;
    var deadline = el.getAttribute('data-deadline');
    this.target = deadline ? new Date(deadline).getTime() : NaN;
    if (isNaN(this.target)) { el.hidden = true; return; }
    this.days = $('[data-days]', el);
    this.hours = $('[data-hours]', el);
    this.minutes = $('[data-minutes]', el);
    this.seconds = $('[data-seconds]', el);
    this.live = $('[data-countdown-live]', el);
    this.finishedText = el.getAttribute('data-finished') || '';
    this.tick();
    this.timer = window.setInterval(this.tick.bind(this), 1000);
  };
  CountdownTimer.prototype.tick = function () {
    var diff = this.target - Date.now();
    if (diff <= 0) {
      window.clearInterval(this.timer);
      var text = $('.countdown__text', this.el);
      var clock = $('.countdown__clock', this.el);
      if (text && this.finishedText) { text.textContent = this.finishedText; }
      if (clock) { clock.hidden = true; }
      return;
    }
    var s = Math.floor(diff / 1000);
    var pad = function (n) { return (n < 10 ? '0' : '') + n; };
    if (this.days) { this.days.textContent = pad(Math.floor(s / 86400)); }
    if (this.hours) { this.hours.textContent = pad(Math.floor(s % 86400 / 3600)); }
    if (this.minutes) { this.minutes.textContent = pad(Math.floor(s % 3600 / 60)); }
    if (this.seconds) { this.seconds.textContent = pad(s % 60); }
    if (this.live && s % 60 === 0) {
      this.live.textContent = Math.floor(s / 60) + ' minutes left to enrol';
    }
  };
  $$('countdown-timer').forEach(function (el) { new CountdownTimer(el); });

  /* ----------------------------------------------------- reveal on scroll */
  var revealTargets = $$('.section > .page-width, .hero__copy, .hero__media, .stats__grid, .pricing__card');
  if (revealTargets.length && 'IntersectionObserver' in window && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-in');
          io.unobserve(entry.target);
        }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.06 });
    revealTargets.forEach(function (el) {
      el.classList.add('reveal');
      io.observe(el);
    });
  }

  /* ------------------------------------------------------- sticky buy bar */
  var buyBar = $('[data-buy-bar]');
  if (buyBar) {
    var sentinel = $('[data-cta="hero-primary"]') || $('.hero') || $('.pricing');
    if (sentinel && 'IntersectionObserver' in window) {
      var barObserver = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          var show = !entry.isIntersecting && entry.boundingClientRect.top < 0;
          buyBar.classList.toggle('is-visible', show);
          document.body.classList.toggle('body--has-buybar', show);
        });
      }, { threshold: 0 });
      barObserver.observe(sentinel);
    } else {
      buyBar.classList.add('is-visible');
      document.body.classList.add('body--has-buybar');
    }
  }

  /* ---------------------------------------------------- click-to-load video */
  $$('[data-video-embed]').forEach(function (wrap) {
    var trigger = $('[data-video-play]', wrap);
    var src = wrap.getAttribute('data-embed-src');
    if (!trigger || !src) { return; }
    trigger.addEventListener('click', function (event) {
      event.preventDefault();
      var iframe = document.createElement('iframe');
      iframe.setAttribute('src', src);
      iframe.setAttribute('title', trigger.textContent.trim() || 'Video');
      iframe.setAttribute('loading', 'lazy');
      iframe.setAttribute('allow', 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share');
      iframe.setAttribute('allowfullscreen', '');
      wrap.innerHTML = '';
      wrap.appendChild(iframe);
      announce('Video loading');
    });
  });

  /* --------------------------------------------------------------- share */
  $$('[data-share]').forEach(function (wrap) {
    var btn = $('[data-share-btn]', wrap);
    if (!btn) { return; }
    btn.addEventListener('click', function () {
      var data = { title: document.title, url: window.location.href };
      if (navigator.share) {
        navigator.share(data).catch(function () {});
      } else if (navigator.clipboard) {
        navigator.clipboard.writeText(data.url).then(function () { announce('Link copied'); });
      }
    });
  });

  /* ------------------------------------------------------------- gallery */
  $$('[data-gallery]').forEach(function (gallery) {
    var main = $('[data-gallery-main]', gallery);
    var thumbs = $$('[data-gallery-thumb]', gallery);
    if (!main || !thumbs.length) { return; }
    thumbs.forEach(function (thumb) {
      thumb.addEventListener('click', function () {
        var img = $('img', main);
        if (!img) { return; }
        img.setAttribute('src', thumb.getAttribute('data-full'));
        var srcset = thumb.getAttribute('data-srcset');
        if (srcset) { img.setAttribute('srcset', srcset); } else { img.removeAttribute('srcset'); }
        thumbs.forEach(function (t) { t.classList.remove('is-active'); });
        thumb.classList.add('is-active');
      });
    });
  });

  /* ------------------------------------------------------ gift card copy */
  var copyGift = $('[data-copy-gift]');
  if (copyGift) {
    copyGift.addEventListener('click', function () {
      var code = $('[data-gift-code]');
      if (!code || !navigator.clipboard) { return; }
      navigator.clipboard.writeText(code.textContent.trim()).then(function () {
        copyGift.textContent = 'Copied';
        announce('Gift card code copied');
      });
    });
  }

  /* -------------------------------------------------------- gift card QR */
  var qrTarget = $('[data-qr-code]');
  if (qrTarget && typeof window.QRCode !== 'undefined') {
    try {
      new window.QRCode(qrTarget, {
        text: qrTarget.getAttribute('data-identifier') || '',
        width: 132,
        height: 132
      });
    } catch (e) { /* keep the page working even if the generator fails */ }
  }

  /* --------------------------------------------------- password recovery */
  var recoverLink = $('[data-toggle-recover]');
  if (recoverLink) {
    recoverLink.addEventListener('click', function (event) {
      event.preventDefault();
      var box = document.getElementById('recover');
      if (!box) { return; }
      box.hidden = false;
      var input = $('input', box);
      if (input) { input.focus(); }
    });
  }

  /* ------------------------------------------------------ quantity inputs */
  var QuantityInput = function (el) {
    this.el = el;
    this.input = $('.quantity__input', el);
    this.min = parseInt(el.getAttribute('data-min') || '1', 10);
    var self = this;
    $$('[data-qty-action]', el).forEach(function (btn) {
      btn.addEventListener('click', function () {
        var step = btn.getAttribute('data-qty-action') === 'plus' ? 1 : -1;
        var next = (parseInt(self.input.value, 10) || 0) + step;
        if (next < self.min) { next = self.min; }
        self.input.value = next;
        self.input.dispatchEvent(new Event('change', { bubbles: true }));
      });
    });
  };
  $$('quantity-input').forEach(function (el) { new QuantityInput(el); });

  /* ----------------------------------------------------------- cart drawer */
  var drawer = $('[data-cart-drawer]');

  function openDrawer() {
    if (!drawer) { return; }
    if (typeof drawer.showModal === 'function') { drawer.showModal(); }
    else { drawer.setAttribute('open', ''); }
    document.documentElement.style.overflow = 'hidden';
  }
  function closeDrawer() {
    if (!drawer) { return; }
    if (typeof drawer.close === 'function' && drawer.open) { drawer.close(); }
    else { drawer.removeAttribute('open'); }
    document.documentElement.style.overflow = '';
  }
  if (drawer) {
    $$('[data-cart-close]', drawer).forEach(function (btn) { btn.addEventListener('click', closeDrawer); });
    drawer.addEventListener('click', function (event) {
      if (event.target === drawer) { closeDrawer(); }
    });
    drawer.addEventListener('close', function () { document.documentElement.style.overflow = ''; });
  }

  function setCartCount(count) {
    $$('[data-cart-count]').forEach(function (el) {
      el.textContent = count;
      el.classList.toggle('is-empty', count === 0);
    });
    $$('[data-cart-link]').forEach(function (link) {
      link.setAttribute('aria-label', 'Cart: ' + count + (count === 1 ? ' item' : ' items'));
    });
  }

  function refreshDrawer() {
    if (!drawer) { return Promise.resolve(); }
    return fetch(window.location.pathname + '?sections=cart-drawer', { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        var html = data && data['cart-drawer'];
        if (!html) { return; }
        var parsed = new DOMParser().parseFromString(html, 'text/html');
        var fresh = parsed.querySelector('[data-cart-drawer-inner]');
        var current = drawer.querySelector('[data-cart-drawer-inner]');
        if (fresh && current) {
          current.innerHTML = fresh.innerHTML;
          bindDrawerEvents();
        }
      })
      .catch(function () {});
  }

  function bindDrawerEvents() {
    if (!drawer) { return; }
    $$('[data-qty-action]', drawer).forEach(function (btn) {
      if (btn.dataset.bound) { return; }
      btn.dataset.bound = '1';
      btn.addEventListener('click', function () {
        var wrapper = btn.closest('.quantity');
        var input = wrapper ? $('.quantity__input', wrapper) : null;
        if (!input) { return; }
        var step = btn.getAttribute('data-qty-action') === 'plus' ? 1 : -1;
        var next = Math.max(0, (parseInt(input.value, 10) || 0) + step);
        input.value = next;
        updateLine(input.getAttribute('data-line-key'), next);
      });
    });
    $$('[data-cart-remove]', drawer).forEach(function (link) {
      if (link.dataset.bound) { return; }
      link.dataset.bound = '1';
      link.addEventListener('click', function (event) {
        event.preventDefault();
        updateLine(link.getAttribute('data-line-key'), 0);
      });
    });
    $$('.quantity__input[data-line-key]', drawer).forEach(function (input) {
      if (input.dataset.bound) { return; }
      input.dataset.bound = '1';
      input.addEventListener('change', function () {
        updateLine(input.getAttribute('data-line-key'), parseInt(input.value, 10) || 0);
      });
    });
  }

  function updateLine(key, quantity) {
    if (!key) { return; }
    fetch(root + 'cart/change.js', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body: JSON.stringify({ id: key, quantity: quantity })
    })
      .then(function (res) { return res.json(); })
      .then(function (cart) {
        if (cart && typeof cart.item_count === 'number') { setCartCount(cart.item_count); }
        return refreshDrawer();
      })
      .catch(function () { announce('Could not update the cart. Please refresh.'); });
  }

  /* -------------------------------------------------------- add to cart */
  function ShopProductForm(form) {
    this.form = form;
    this.wrapper = form.closest('product-form') || form.parentElement;
    this.button = $('[data-form-status]', form);
    this.errorBox = $('[data-form-error]', form);
    var self = this;
    form.addEventListener('submit', function (event) {
      event.preventDefault();
      self.submit();
    });
  }
  ShopProductForm.prototype.submit = function () {
    var self = this;
    var submitButton = $('[data-form-status]', this.form);
    var button = submitButton ? submitButton.closest('button') : null;
    var original = submitButton ? submitButton.textContent.trim() : '';
    if (button) {
      button.disabled = true;
      if (submitButton) { submitButton.textContent = button.getAttribute('data-label-adding') || 'Adding…'; }
    }
    if (this.errorBox) { this.errorBox.hidden = true; }

    fetch(root + 'cart/add.js', {
      method: 'POST',
      headers: { 'Accept': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
      body: new FormData(this.form)
    })
      .then(function (res) {
        return res.json().then(function (body) { return { ok: res.ok, body: body }; });
      })
      .then(function (result) {
        if (!result.ok) {
          throw new Error(result.body && (result.body.description || result.body.message) || 'Unable to add to cart');
        }
        return fetch(root + 'cart.js', { headers: { 'Accept': 'application/json' } });
      })
      .then(function (res) { return res.json(); })
      .then(function (cart) {
        setCartCount(cart.item_count);
        announce(original + ' — added to cart');
        if (drawer) {
          return refreshDrawer().then(openDrawer);
        }
        window.location.href = root + 'cart';
      })
      .catch(function (error) {
        if (self.errorBox) {
          self.errorBox.textContent = error.message || 'Something went wrong. Please try again.';
          self.errorBox.hidden = false;
        }
        announce('Could not add to cart');
      })
      .then(function () {
        if (button) { button.disabled = false; }
        if (submitButton) { submitButton.textContent = original; }
      });
  };
  $$('form[data-type="add-to-cart-form"], form.product-form__inner, form[id^="course-buy-form"]').forEach(function (form) {
    new ShopProductForm(form);
  });

  /* --------------------------------------------------------- variant pick */
  function VariantSelects(el) {
    this.el = el;
    var data = $('[data-variant-data]', el);
    if (!data) { return; }
    try { this.variants = JSON.parse(data.textContent); } catch (e) { this.variants = []; }
    this.form = el.closest('form');
    this.idInput = this.form ? $('[data-variant-id]', this.form) : null;
    this.submit = this.form ? $('.product-form__submit', this.form) : null;
    var self = this;
    $$('select[data-option-index]', el).forEach(function (select) {
      select.addEventListener('change', function () { self.onChange(); });
    });
  }
  VariantSelects.prototype.onChange = function () {
    var selected = $$('select[data-option-index]', this.el).map(function (select) {
      return { index: parseInt(select.getAttribute('data-option-index'), 10), value: select.value };
    });
    var match = this.variants.filter(function (variant) {
      return selected.every(function (option) {
        return variant.options[option.index] === option.value;
      });
    })[0];
    if (!match) { return; }
    if (this.idInput) {
      this.idInput.value = match.id;
      if (match.available) { this.idInput.removeAttribute('disabled'); }
      else { this.idInput.setAttribute('disabled', 'disabled'); }
    }
    var priceEl = this.form ? $('.price__now', this.form.closest('.product__info') || document) : null;
    if (!priceEl) { priceEl = document.querySelector('.product__price-row .price__now'); }
    if (priceEl && typeof match.price === 'number') { priceEl.textContent = formatMoney(match.price); }
    if (this.submit) {
      var label = $('[data-form-status]', this.submit) || this.submit;
      this.submit.disabled = !match.available;
      if (match.available) { label.textContent = this.submit.getAttribute('data-label-add') || 'Add to cart'; }
      else { label.textContent = this.submit.getAttribute('data-label-sold-out') || 'Sold out'; }
    }
    var url = new URL(window.location.href);
    url.searchParams.set('variant', match.id);
    window.history.replaceState({}, '', url.toString());
  };
  $$('variant-selects').forEach(function (el) { new VariantSelects(el); });

  /* ---------------------------------------------------- cart page remove */
  $$('.cart-page__lines [data-cart-remove]').forEach(function (link) {
    link.addEventListener('click', function (event) {
      event.preventDefault();
      fetch(link.getAttribute('href'), { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        .then(function () { window.location.reload(); })
        .catch(function () { window.location.href = link.getAttribute('href'); });
    });
  });
})();
