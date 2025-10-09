/**
 * FH SWF Chainlit Frontend Enhancements
 * Erweiterte Funktionalitäten für bessere User Experience
 */

(function() {
    'use strict';

    // Warten auf DOM-Load
    document.addEventListener('DOMContentLoaded', function() {
        initializeFHSWFEnhancements();
    });

    /**
     * Hauptinitialisierung aller FH SWF Verbesserungen
     */
    function initializeFHSWFEnhancements() {
        console.log('🎓 Initialisiere FH SWF Enhancements...');
        
        // Features aktivieren
        addWelcomeMessage();
        enhanceErrorHandling();
        addKeyboardShortcuts();
        improveLoadingStates();
        addServiceStatus();
        enhanceAccessibility();
        
        console.log('✅ FH SWF Enhancements erfolgreich geladen');
    }

    /**
     * Begrüßungsnachricht für neue Benutzer
     */
    function addWelcomeMessage() {
        // Prüfen ob erste Session
        if (!localStorage.getItem('fh-swf-visited')) {
            setTimeout(() => {
                showWelcomeDialog();
                localStorage.setItem('fh-swf-visited', 'true');
            }, 2000);
        }
    }

    function showWelcomeDialog() {
        const welcomeHtml = `
            <div id="fh-welcome-overlay" style="
                position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                background: rgba(0, 51, 102, 0.9); z-index: 10000;
                display: flex; align-items: center; justify-content: center;
            ">
                <div style="
                    background: white; border-radius: 12px; padding: 2rem;
                    max-width: 500px; margin: 1rem; text-align: center;
                    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
                ">
                    <h2 style="color: #003366; margin-bottom: 1rem; font-size: 1.5rem;">
                        🎓 Willkommen an der FH SWF!
                    </h2>
                    <p style="color: #666; margin-bottom: 1.5rem; line-height: 1.6;">
                        Ich bin Ihr KI-Assistant und helfe Ihnen gerne bei Fragen rund um 
                        Studium, Campus-Services und die Fachhochschule Südwestfalen.
                    </p>
                    <button id="fh-welcome-start" style="
                        background: linear-gradient(135deg, #0066CC, #003366);
                        color: white; border: none; padding: 12px 24px;
                        border-radius: 6px; font-weight: 500; cursor: pointer;
                        transition: transform 0.2s ease;
                    ">
                        Chat starten 🚀
                    </button>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', welcomeHtml);
        
        document.getElementById('fh-welcome-start').addEventListener('click', () => {
            document.getElementById('fh-welcome-overlay').remove();
        });
    }

    /**
     * Verbesserte Fehlerbehandlung
     */
    function enhanceErrorHandling() {
        // Globale Fehlerbehandlung
        window.addEventListener('error', function(e) {
            console.warn('FH SWF: Fehler abgefangen:', e.error);
            showErrorNotification('Ein technischer Fehler ist aufgetreten. Bitte versuchen Sie es erneut.');
        });

        // Unhandled Promise Rejections
        window.addEventListener('unhandledrejection', function(e) {
            console.warn('FH SWF: Unbehandelte Promise Rejection:', e.reason);
            showErrorNotification('Verbindungsproblem. Prüfen Sie Ihre Internetverbindung.');
        });
    }

    function showErrorNotification(message) {
        const notification = document.createElement('div');
        notification.className = 'fh-error-notification';
        notification.innerHTML = `
            <div style="
                position: fixed; top: 20px; right: 20px; z-index: 9999;
                background: #CC0000; color: white; padding: 1rem 1.5rem;
                border-radius: 8px; box-shadow: 0 4px 12px rgba(204, 0, 0, 0.3);
                max-width: 350px; cursor: pointer;
            ">
                <strong>⚠️ Hinweis:</strong><br>
                ${message}
                <div style="font-size: 0.8rem; margin-top: 0.5rem; opacity: 0.9;">
                    Klicken zum Schließen
                </div>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-Remove nach 5 Sekunden
        setTimeout(() => notification.remove(), 5000);
        
        // Click-to-Remove
        notification.addEventListener('click', () => notification.remove());
    }

    /**
     * Tastaturkürzel für Power-User
     */
    function addKeyboardShortcuts() {
        document.addEventListener('keydown', function(e) {
            // Strg/Cmd + Enter = Nachricht senden
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                const sendButton = document.querySelector('[type="submit"]');
                if (sendButton) {
                    sendButton.click();
                    e.preventDefault();
                }
            }
            
            // Strg/Cmd + K = Eingabefeld fokussieren
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                const input = document.querySelector('input[type="text"], textarea');
                if (input) {
                    input.focus();
                    e.preventDefault();
                }
            }
            
            // Strg/Cmd + N = Neuer Chat
            if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
                const newChatButton = document.querySelector('[title*="Neu"], [aria-label*="neu"]');
                if (newChatButton) {
                    newChatButton.click();
                    e.preventDefault();
                }
            }
        });
    }

    /**
     * Verbesserte Loading-Zustände
     */
    function improveLoadingStates() {
        // Observer für Loading-Elemente
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === 1) { // Element node
                        // Loading-Indikatoren erkennen und verbessern
                        const loadingElements = node.querySelectorAll('[class*="loading"], [class*="spinner"]');
                        loadingElements.forEach(enhanceLoadingElement);
                    }
                });
            });
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    function enhanceLoadingElement(element) {
        if (element.dataset.fhEnhanced) return;
        element.dataset.fhEnhanced = 'true';
        
        // FH SWF Loading-Text hinzufügen
        const loadingTexts = [
            'Durchsuche FH SWF Website...',
            'Analysiere Ihre Anfrage...',
            'Sammle aktuelle Informationen...',
            'Bereite Antwort vor...'
        ];
        
        let currentIndex = 0;
        const textElement = document.createElement('div');
        textElement.style.cssText = `
            margin-top: 8px; font-size: 0.9rem; color: #0066CC;
            font-style: italic; text-align: center;
        `;
        textElement.textContent = loadingTexts[0];
        element.appendChild(textElement);
        
        const interval = setInterval(() => {
            currentIndex = (currentIndex + 1) % loadingTexts.length;
            textElement.textContent = loadingTexts[currentIndex];
        }, 2000);
        
        // Cleanup when loading ends
        const checkLoading = setInterval(() => {
            if (!element.isConnected || !element.offsetParent) {
                clearInterval(interval);
                clearInterval(checkLoading);
            }
        }, 1000);
    }

    /**
     * Service-Status-Anzeige
     */
    function addServiceStatus() {
        const statusContainer = document.createElement('div');
        statusContainer.id = 'fh-service-status';
        statusContainer.style.cssText = `
            position: fixed; bottom: 20px; left: 20px; z-index: 1000;
            background: white; border: 1px solid #E0E0E0; border-radius: 8px;
            padding: 8px 12px; font-size: 0.8rem; color: #666;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            display: none; /* Standardmäßig ausgeblendet */
        `;
        
        document.body.appendChild(statusContainer);
        
        // Status periodisch prüfen
        checkServiceStatus();
        setInterval(checkServiceStatus, 30000); // Alle 30 Sekunden
    }

    function checkServiceStatus() {
        // Vereinfachte Service-Status-Prüfung
        const statusElement = document.getElementById('fh-service-status');
        if (!statusElement) return;
        
        // Online-Status prüfen
        if (!navigator.onLine) {
            statusElement.innerHTML = '🔴 Offline - Keine Internetverbindung';
            statusElement.style.display = 'block';
        } else {
            statusElement.innerHTML = '🟢 Online - Alle Services verfügbar';
            statusElement.style.display = 'none'; // Nur bei Problemen anzeigen
        }
    }

    /**
     * Barrierefreiheit verbessern
     */
    function enhanceAccessibility() {
        // Fokus-Indikatoren verbessern
        const style = document.createElement('style');
        style.textContent = `
            *:focus {
                outline: 2px solid #0066CC !important;
                outline-offset: 2px !important;
            }
            
            .fh-sr-only {
                position: absolute !important;
                width: 1px !important;
                height: 1px !important;
                padding: 0 !important;
                margin: -1px !important;
                overflow: hidden !important;
                clip: rect(0,0,0,0) !important;
                border: 0 !important;
            }
        `;
        document.head.appendChild(style);
        
        // Alt-Texte für wichtige Elemente hinzufügen
        setTimeout(() => {
            document.querySelectorAll('img:not([alt])').forEach(img => {
                if (img.src.includes('logo')) {
                    img.alt = 'FH Südwestfalen Logo';
                } else {
                    img.alt = 'Bild';
                }
            });
        }, 2000);
    }

    // Online/Offline Event-Handler
    window.addEventListener('online', () => {
        console.log('🟢 FH SWF: Verbindung wiederhergestellt');
        const statusElement = document.getElementById('fh-service-status');
        if (statusElement) {
            statusElement.style.display = 'none';
        }
    });

    window.addEventListener('offline', () => {
        console.log('🔴 FH SWF: Verbindung unterbrochen');
        showErrorNotification('Internetverbindung unterbrochen. Einige Funktionen sind möglicherweise nicht verfügbar.');
    });

})();