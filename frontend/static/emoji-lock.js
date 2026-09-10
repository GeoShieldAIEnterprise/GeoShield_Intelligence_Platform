/* GeoShield AI -- Emoji & UI Text Lock */
window.GeoShieldEmojiLock = {
    locked: true,
    originalContent: {},
    init() {
        // Restore clean HTML entities for sidebar & header icons
        const icons = {
            "navDashboard": "&#128202; Dashboard",
            "navLiveMap": "&#128640; Live Map",
            "navAnalytics": "&#128200; Analytics",
            "navAlerts": "&#128276; Alerts",
            "navReports": "&#128196; Reports",
            "navFlood": "&#127754; Flood Engine",
            "navFire": "&#128293; Fire Engine",
            "navEarthquake": "&#127757; Earthquake Engine",
            "navAgriculture": "&#127806; Agriculture",
            "navSettings": "&#9881;&#65039; Settings"
        };

        for (const [id, html] of Object.entries(icons)) {
            const el = document.getElementById(id);
            if (el) {
                el.innerHTML = html;
                this.originalContent[id] = html;
            }
        }

        // Create lock toggle in header if not present
        if (!document.getElementById("emojiLockToggle")) {
            const headerControls = document.querySelector(".geoshield-header-controls") || document.body;
            const lockBtn = document.createElement("button");
            lockBtn.id = "emojiLockToggle";
            lockBtn.className = "geoshield-lock-btn";
            lockBtn.innerHTML = "&#128274; Emoji Lock: ON";
            lockBtn.title = "Click to unlock UI emojis and text modifications";
            lockBtn.style.cssText = "background: #1e293b; color: #38bdf8; border: 1px solid #334155; padding: 4px 10px; border-radius: 6px; cursor: pointer; font-size: 12px; margin-left: 8px;";
            
            lockBtn.addEventListener("click", () => {
                this.locked = !this.locked;
                lockBtn.innerHTML = this.locked ? "&#128274; Emoji Lock: ON" : "&#128275; Emoji Lock: OFF";
                lockBtn.style.color = this.locked ? "#38bdf8" : "#f87171";
                console.log("GeoShield Emoji Lock state:", this.locked ? "LOCKED" : "UNLOCKED");
            });

            headerControls.appendChild(lockBtn);
        }

        // MutationObserver to protect locked items
        const observer = new MutationObserver((mutations) => {
            if (!this.locked) return;
            mutations.forEach((mutation) => {
                if (mutation.target && mutation.target.id && this.originalContent[mutation.target.id]) {
                    if (mutation.target.innerHTML !== this.originalContent[mutation.target.id]) {
                        mutation.target.innerHTML = this.originalContent[mutation.target.id];
                    }
                }
            });
        });

        for (const id of Object.keys(icons)) {
            const el = document.getElementById(id);
            if (el) {
                observer.observe(el, { childList: true, subtree: true, characterData: true });
            }
        }

        console.log("GeoShield Emoji Lock initialized.");
    }
};

document.addEventListener("DOMContentLoaded", () => {
    window.GeoShieldEmojiLock.init();
});
