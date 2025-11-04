// ===== ANIMASI CHART & INTERAKSI =====

class ChartAnimations {
  constructor() {
    this.init();
  }

  init() {
    this.animateCharts();
    this.initChartHoverEffects();
    this.initScrollAnimations();
    this.initCounterAnimations();
  }

  // Animasi khusus untuk chart/gambar
  animateCharts() {
    const charts = document.querySelectorAll(".chart-img");

    charts.forEach((chart, index) => {
      // Reset untuk animasi
      chart.style.opacity = "0";
      chart.style.transform = "translateY(30px) scale(0.95)";

      // Stagger animation
      setTimeout(() => {
        chart.style.transition = "all 0.8s cubic-bezier(0.4, 0, 0.2, 1)";
        chart.style.opacity = "1";
        chart.style.transform = "translateY(0) scale(1)";

        // Add continuous subtle animation
        this.addBreathingAnimation(chart);
      }, index * 200);
    });
  }

  // Efek breathing untuk chart
  addBreathingAnimation(element) {
    let scale = 1;
    const animate = () => {
      scale = scale === 1 ? 1.02 : 1;
      element.style.transform = `scale(${scale})`;
    };

    setInterval(animate, 2000);
  }

  // Efek hover pada chart container
  initChartHoverEffects() {
    const chartContainers = document.querySelectorAll(".chart-container");

    chartContainers.forEach((container) => {
      const img = container.querySelector("img");

      container.addEventListener("mouseenter", () => {
        img.style.transform = "scale(1.05) rotate(1deg)";
        img.style.filter = "brightness(1.1) saturate(1.2)";
        container.style.boxShadow = "0 15px 40px rgba(255, 107, 157, 0.3)";
      });

      container.addEventListener("mouseleave", () => {
        img.style.transform = "scale(1) rotate(0deg)";
        img.style.filter = "brightness(1) saturate(1)";
        container.style.boxShadow = "0 8px 30px rgba(255, 107, 157, 0.15)";
      });
    });
  }

  // Animasi counter untuk numbers
  initCounterAnimations() {
    const counters = document.querySelectorAll(".counter");

    counters.forEach((counter) => {
      const target = parseInt(counter.getAttribute("data-target"));
      const duration = 2000;
      const step = target / (duration / 16);
      let current = 0;

      const updateCounter = () => {
        current += step;
        if (current < target) {
          counter.textContent = Math.floor(current).toLocaleString();
          requestAnimationFrame(updateCounter);
        } else {
          counter.textContent = target.toLocaleString();
        }
      };

      // Start animation when element is in viewport
      const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            updateCounter();
            observer.unobserve(entry.target);
          }
        });
      });

      observer.observe(counter);
    });
  }

  // Animasi saat scroll
  initScrollAnimations() {
    const observerOptions = {
      threshold: 0.1,
      rootMargin: "0px 0px -50px 0px",
    };

    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("animated");
          if (entry.target.classList.contains("summary-card")) {
            entry.target.style.animationPlayState = "running";
          }
        }
      });
    }, observerOptions);

    // Observe semua elemen yang perlu animasi
    document
      .querySelectorAll(
        ".card, .summary-card, .chart-container, .table-responsive"
      )
      .forEach((el) => {
        observer.observe(el);
      });
  }
}

// ===== NOTIFICATION SYSTEM =====
class NotificationSystem {
  constructor() {
    this.init();
  }

  init() {
    window.showNotification = (message, type = "info", duration = 5000) => {
      this.createNotification(message, type, duration);
    };

    // Convert flash messages to notifications
    this.convertFlashMessages();
  }

  createNotification(message, type, duration) {
    const notification = document.createElement("div");
    notification.className = `alert alert-${type} notification-alert`;
    notification.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="fas fa-${this.getNotificationIcon(type)} me-3"></i>
                <span class="flex-grow-1">${message}</span>
                <button class="btn-close btn-close-white" onclick="this.parentElement.parentElement.remove()"></button>
            </div>
        `;

    Object.assign(notification.style, {
      position: "fixed",
      top: "20px",
      right: "20px",
      zIndex: "9999",
      minWidth: "350px",
      maxWidth: "500px",
      boxShadow: "0 10px 30px rgba(0,0,0,0.3)",
      borderRadius: "15px",
      animation: "slideInRight 0.5s ease-out",
      backdropFilter: "blur(10px)",
    });

    document.body.appendChild(notification);

    // Auto remove
    setTimeout(() => {
      if (notification.parentElement) {
        notification.style.animation = "slideOutRight 0.5s ease-in";
        setTimeout(() => notification.remove(), 500);
      }
    }, duration);
  }

  getNotificationIcon(type) {
    const icons = {
      success: "check-circle",
      error: "exclamation-circle",
      warning: "exclamation-triangle",
      info: "info-circle",
    };
    return icons[type] || "info-circle";
  }

  convertFlashMessages() {
    const flashMessages = document.querySelectorAll(".alert");
    flashMessages.forEach((alert, index) => {
      setTimeout(() => {
        const category = alert.classList.contains("alert-success")
          ? "success"
          : alert.classList.contains("alert-danger")
          ? "error"
          : alert.classList.contains("alert-warning")
          ? "warning"
          : "info";

        const message = alert.querySelector("span")
          ? alert.querySelector("span").textContent
          : alert.textContent;

        this.createNotification(message, category, 5000);
        alert.remove();
      }, index * 300);
    });
  }
}

// ===== ANALISIS PROGRESS NOTIFICATIONS =====
class AnalysisProgress {
  constructor() {
    this.progressNotifications = [];
    this.currentStep = 0;
  }

  showAnalysisProgress() {
    this.currentStep = 0;
    this.progressNotifications = [];

    const steps = [
      { message: "📤 Mengupload file...", delay: 0 },
      { message: "🔍 Memproses data...", delay: 1500 },
      { message: "🤖 Menjalankan analisis ML...", delay: 3000 },
      { message: "📊 Melakukan segmentasi produk...", delay: 5000 },
    ];

    steps.forEach((step) => {
      setTimeout(() => {
        this.showStep(step.message, "info");
      }, step.delay);
    });
  }

  showStep(message, type) {
    // Remove previous progress notifications
    this.progressNotifications.forEach((notification) => {
      if (notification.parentElement) {
        notification.style.animation = "slideOutRight 0.3s ease-in";
        setTimeout(() => {
          if (notification.parentElement) notification.remove();
        }, 300);
      }
    });

    const notification = document.createElement("div");
    notification.className = `alert alert-${type} progress-notification`;
    notification.innerHTML = `
            <div class="d-flex align-items-center">
                <div class="loading-spinner me-3"></div>
                <span class="flex-grow-1">${message}</span>
            </div>
        `;

    Object.assign(notification.style, {
      position: "fixed",
      top: "80px",
      right: "20px",
      zIndex: "9998",
      minWidth: "300px",
      boxShadow: "0 8px 25px rgba(0,0,0,0.2)",
      borderRadius: "12px",
      animation: "slideInRight 0.3s ease-out",
      backdropFilter: "blur(10px)",
      border: "1px solid rgba(255, 107, 157, 0.2)",
    });

    document.body.appendChild(notification);
    this.progressNotifications = [notification]; // Hanya simpan yang terbaru
  }

  completeAnalysis() {
    // Remove progress notification
    this.progressNotifications.forEach((notification) => {
      if (notification.parentElement) {
        notification.style.animation = "slideOutRight 0.5s ease-in";
        setTimeout(() => notification.remove(), 500);
      }
    });
    this.progressNotifications = [];

    // Show success notification
    showNotification(
      "🎉 Analisis data berhasil diselesaikan! Data siap ditampilkan.",
      "success",
      5000
    );
  }

  showError(message) {
    // Remove progress notifications
    this.progressNotifications.forEach((notification) => {
      if (notification.parentElement) {
        notification.remove();
      }
    });
    this.progressNotifications = [];

    // Show error notification
    showNotification(`❌ ${message}`, "error", 5000);
  }
}

// ===== NAVBAR ANIMATIONS =====
class NavbarAnimations {
  constructor() {
    this.init();
  }

  init() {
    this.addNavbarEffects();
    this.addActivePageIndicator();
    this.addMobileMenuAnimation();
  }

  addNavbarEffects() {
    const navbar = document.querySelector(".navbar");
    const navLinks = document.querySelectorAll(".nav-link");

    // Hover effects
    navLinks.forEach((link) => {
      link.addEventListener("mouseenter", (e) => {
        e.target.style.transform = "translateY(-2px) scale(1.05)";
        e.target.style.background = "rgba(255, 255, 255, 0.2)";
      });

      link.addEventListener("mouseleave", (e) => {
        e.target.style.transform = "translateY(0) scale(1)";
        if (!e.target.classList.contains("active")) {
          e.target.style.background = "transparent";
        }
      });
    });

    // Scroll effect
    let lastScroll = 0;
    window.addEventListener("scroll", () => {
      const scrolled = window.pageYOffset;
      const navbarHeight = navbar.offsetHeight;

      if (scrolled > 50) {
        navbar.style.background = "rgba(255, 107, 157, 0.95)";
        navbar.style.backdropFilter = "blur(20px)";
      } else {
        navbar.style.background = "";
        navbar.style.backdropFilter = "blur(10px)";
      }

      lastScroll = scrolled;
    });
  }

  addActivePageIndicator() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll(".nav-link");

    navLinks.forEach((link) => {
      if (link.getAttribute("href") === currentPath) {
        link.classList.add("active");
        link.style.background = "rgba(255, 255, 255, 0.2)";
        link.style.boxShadow = "0 4px 15px rgba(0,0,0,0.2)";
      }
    });
  }

  addMobileMenuAnimation() {
    const navbarToggler = document.querySelector(".navbar-toggler");
    const navbarCollapse = document.querySelector(".navbar-collapse");

    if (navbarToggler && navbarCollapse) {
      navbarToggler.addEventListener("click", () => {
        navbarCollapse.classList.toggle("show");
        navbarToggler.classList.toggle("collapsed");
      });
    }
  }
}

// ===== TABLE ANIMATIONS =====
class TableAnimations {
  constructor() {
    this.init();
  }

  init() {
    this.addTableRowAnimations();
    this.addSortingIndicators();
  }

  addTableRowAnimations() {
    const tableRows = document.querySelectorAll(".table tbody tr");

    tableRows.forEach((row, index) => {
      row.style.opacity = "0";
      row.style.transform = "translateX(-20px)";

      setTimeout(() => {
        row.style.transition = "all 0.5s ease";
        row.style.opacity = "1";
        row.style.transform = "translateX(0)";
      }, index * 100);

      // Hover effect
      row.addEventListener("mouseenter", () => {
        row.style.transform = "scale(1.02) translateX(10px)";
        row.style.zIndex = "1";
        row.style.boxShadow = "0 5px 15px rgba(255, 107, 157, 0.1)";
      });

      row.addEventListener("mouseleave", () => {
        row.style.transform = "scale(1) translateX(0)";
        row.style.zIndex = "0";
        row.style.boxShadow = "none";
      });
    });
  }

  addSortingIndicators() {
    const tableHeaders = document.querySelectorAll(".table thead th");

    tableHeaders.forEach((header) => {
      header.style.cursor = "pointer";
      header.addEventListener("click", () => {
        this.sortTable(header);
      });
    });
  }

  sortTable(header) {
    showNotification("Fitur sorting akan segera tersedia!", "info", 2000);
  }
}

// ===== DATASET SELECTOR ANIMATIONS =====
class DatasetAnimations {
  constructor() {
    this.init();
  }

  init() {
    this.addDatasetButtonEffects();
    this.addCombinedDataAnimation();
  }

  addDatasetButtonEffects() {
    const datasetButtons = document.querySelectorAll(".dataset-btn");

    datasetButtons.forEach((btn) => {
      btn.addEventListener("mouseenter", () => {
        if (!btn.classList.contains("active")) {
          btn.style.transform = "translateY(-3px) scale(1.05)";
          btn.style.boxShadow = "0 8px 20px rgba(255, 107, 157, 0.3)";
        }
      });

      btn.addEventListener("mouseleave", () => {
        if (!btn.classList.contains("active")) {
          btn.style.transform = "translateY(0) scale(1)";
          btn.style.boxShadow = "none";
        }
      });

      btn.addEventListener("click", (e) => {
        // Add loading state
        const originalHTML = btn.innerHTML;
        btn.innerHTML = '<span class="loading-spinner me-2"></span> Loading...';
        btn.disabled = true;

        // Reset setelah delay
        setTimeout(() => {
          btn.innerHTML = originalHTML;
          btn.disabled = false;
        }, 2000);
      });
    });
  }

  addCombinedDataAnimation() {
    const combineBtn = document.querySelector('a[href*="combined_data"]');
    if (combineBtn) {
      combineBtn.addEventListener("click", (e) => {
        e.preventDefault();

        showNotification("Menggabungkan dataset...", "info", 2000);

        // Simulate processing
        setTimeout(() => {
          window.location.href = combineBtn.href;
        }, 1500);
      });
    }
  }
}

// ===== INITIALIZATION =====
document.addEventListener("DOMContentLoaded", function () {
  // Initialize all animation systems
  new ChartAnimations();
  new NotificationSystem();
  new NavbarAnimations();
  new TableAnimations();
  new DatasetAnimations();

  // Initialize analysis progress
  window.analysisProgress = new AnalysisProgress();

  // Add additional animations
  initFormAnimations();
  initFloatingElements();
  initExportButtonAnimation();
  initDeleteConfirmations();

  // Auto-trigger analysis progress pada halaman upload
  initAnalysisProgress();

  // Handle page specific animations
  initPageSpecificAnimations();

  console.log("🌸 Sales ML Analyzer - Animations Initialized");
});

// Analysis progress untuk form upload
function initAnalysisProgress() {
  const uploadForm = document.querySelector(
    'form[enctype="multipart/form-data"]'
  );

  if (uploadForm) {
    uploadForm.addEventListener("submit", function (e) {
      const fileInput = this.querySelector('input[type="file"]');
      const button = this.querySelector('button[type="submit"]');

      if (fileInput && fileInput.files.length > 0) {
        // Show loading state pada button
        if (button) {
          const originalHTML = button.innerHTML;
          button.innerHTML = `
                        <span class="loading-spinner me-2"></span>
                        Menganalisis...
                    `;
          button.disabled = true;

          // Reset button setelah 10 detik (fallback)
          setTimeout(() => {
            button.innerHTML = originalHTML;
            button.disabled = false;
          }, 10000);
        }

        // Start progress notifications
        window.analysisProgress.showAnalysisProgress();

        // Auto complete setelah form submit (simulasi)
        // Di production, ini akan dipanggil dari response server
        setTimeout(() => {
          window.analysisProgress.completeAnalysis();
        }, 7000);
      }
    });
  }
}

// Form animations
function initFormAnimations() {
  const forms = document.querySelectorAll("form");
  forms.forEach((form) => {
    form.addEventListener("submit", function (e) {
      const button = this.querySelector('button[type="submit"]');
      if (button) {
        const originalText = button.innerHTML;
        button.innerHTML = `
                    <span class="loading-spinner me-2"></span>
                    Memproses...
                `;
        button.disabled = true;

        // Auto reset setelah 5 detik (fallback)
        setTimeout(() => {
          button.innerHTML = originalText;
          button.disabled = false;
        }, 5000);
      }
    });
  });
}

// Floating elements animation
function initFloatingElements() {
  const elements = document.querySelectorAll(".summary-card");
  elements.forEach((el, index) => {
    el.style.animationDelay = `${index * 0.2}s`;
  });
}

// Export button animation
function initExportButtonAnimation() {
  const exportBtn = document.querySelector('a[href*="export-results"]');
  if (exportBtn) {
    exportBtn.addEventListener("click", (e) => {
      e.preventDefault();

      showNotification("Mempersiapkan file export...", "info", 2000);

      // Simulate processing
      setTimeout(() => {
        window.location.href = exportBtn.href;
      }, 1500);
    });
  }
}

// Delete confirmation animations
function initDeleteConfirmations() {
  const deleteForms = document.querySelectorAll('form[action*="clear"]');

  deleteForms.forEach((form) => {
    form.addEventListener("submit", async function (e) {
      e.preventDefault();

      const isConfirmed = await showConfirmationDialog(
        "Apakah Anda yakin ingin menghapus data?",
        "Tindakan ini tidak dapat dibatalkan dan semua data akan hilang secara permanen."
      );

      if (isConfirmed) {
        const button = this.querySelector('button[type="submit"]');
        if (button) {
          button.innerHTML =
            '<span class="loading-spinner me-2"></span>Menghapus...';
          button.disabled = true;
        }
        this.submit();
      }
    });
  });
}

// Page specific animations
function initPageSpecificAnimations() {
  // Dashboard page animations
  if (window.location.pathname.includes("dashboard")) {
    initDashboardAnimations();
  }

  // Upload page animations
  if (window.location.pathname.includes("upload")) {
    initUploadPageAnimations();
  }
}

function initDashboardAnimations() {
  // Add pulse animation to important numbers
  const importantNumbers = document.querySelectorAll(".summary-card h3");
  importantNumbers.forEach((number) => {
    setInterval(() => {
      number.style.transform = "scale(1.1)";
      setTimeout(() => {
        number.style.transform = "scale(1)";
      }, 500);
    }, 3000);
  });

  // Add click animation to cards
  const cards = document.querySelectorAll(".card");
  cards.forEach((card) => {
    card.addEventListener("click", function () {
      this.style.transform = "scale(0.98)";
      setTimeout(() => {
        this.style.transform = "";
      }, 150);
    });
  });
}

function initUploadPageAnimations() {
  // Add drag and drop effects
  const fileInput = document.querySelector('input[type="file"]');
  const uploadCard = document.querySelector(".card");

  if (fileInput && uploadCard) {
    uploadCard.addEventListener("dragover", (e) => {
      e.preventDefault();
      uploadCard.style.transform = "scale(1.05)";
      uploadCard.style.borderColor = "#ff6b9d";
      uploadCard.style.background =
        "linear-gradient(135deg, #fff5f7 0%, #ffeef2 100%)";
    });

    uploadCard.addEventListener("dragleave", (e) => {
      e.preventDefault();
      uploadCard.style.transform = "scale(1)";
      uploadCard.style.borderColor = "";
      uploadCard.style.background = "";
    });

    uploadCard.addEventListener("drop", (e) => {
      e.preventDefault();
      uploadCard.style.transform = "scale(1)";
      uploadCard.style.borderColor = "";
      uploadCard.style.background = "";

      // Trigger file input
      if (e.dataTransfer.files.length > 0) {
        fileInput.files = e.dataTransfer.files;
        showNotification("File siap diupload!", "success", 2000);
      }
    });
  }
}

// Confirmation dialog
function showConfirmationDialog(title, message) {
  return new Promise((resolve) => {
    const modal = document.createElement("div");
    modal.className = "confirmation-modal";
    modal.innerHTML = `
            <div class="confirmation-overlay">
                <div class="confirmation-dialog">
                    <div class="confirmation-header">
                        <i class="fas fa-exclamation-triangle text-warning fa-beat"></i>
                        <h5>${title}</h5>
                    </div>
                    <div class="confirmation-body">
                        <p>${message}</p>
                    </div>
                    <div class="confirmation-footer">
                        <button class="btn btn-outline-secondary" id="confirmCancel">
                            <i class="fas fa-times me-2"></i>Batal
                        </button>
                        <button class="btn btn-danger" id="confirmOk">
                            <i class="fas fa-trash me-2"></i>Ya, Hapus
                        </button>
                    </div>
                </div>
            </div>
        `;

    document.body.appendChild(modal);

    document.getElementById("confirmCancel").onclick = () => {
      modal.remove();
      resolve(false);
    };

    document.getElementById("confirmOk").onclick = () => {
      modal.remove();
      resolve(true);
    };
  });
}

// Utility function untuk copy text
function copyToClipboard(text) {
  navigator.clipboard.writeText(text).then(() => {
    showNotification("📋 Teks berhasil disalin!", "success", 2000);
  });
}

// Add CSS for animations
function injectCustomStyles() {
  const styles = `
        @keyframes slideInRight {
            from {
                opacity: 0;
                transform: translateX(100%);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        
        @keyframes slideOutRight {
            from {
                opacity: 1;
                transform: translateX(0);
            }
            to {
                opacity: 0;
                transform: translateX(100%);
            }
        }

        .confirmation-modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 9999;
            animation: fadeIn 0.3s ease;
        }

        .confirmation-overlay {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            backdrop-filter: blur(5px);
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 1rem;
        }

        .confirmation-dialog {
            background: white;
            border-radius: 20px;
            padding: 2rem;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 400px;
            width: 100%;
            animation: scaleIn 0.3s ease;
        }

        .confirmation-header {
            text-align: center;
            margin-bottom: 1rem;
        }

        .confirmation-header i {
            font-size: 3rem;
            margin-bottom: 1rem;
        }

        .confirmation-body {
            text-align: center;
            margin-bottom: 2rem;
            color: #666;
        }

        .confirmation-footer {
            display: flex;
            gap: 1rem;
            justify-content: center;
        }

        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        @keyframes scaleIn {
            from {
                opacity: 0;
                transform: scale(0.8);
            }
            to {
                opacity: 1;
                transform: scale(1);
            }
        }

        .progress-notification {
            border-left: 4px solid #ff6b9d !important;
        }

        .table tbody tr {
            transition: all 0.3s ease;
        }
    `;

  const styleSheet = document.createElement("style");
  styleSheet.textContent = styles;
  document.head.appendChild(styleSheet);
}

// Inject custom styles
injectCustomStyles();

// Export untuk penggunaan global
window.ChartAnimations = ChartAnimations;
window.NotificationSystem = NotificationSystem;
window.AnalysisProgress = AnalysisProgress;
window.showNotification = showNotification;
window.copyToClipboard = copyToClipboard;
