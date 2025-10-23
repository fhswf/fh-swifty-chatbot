"""Script simple pour tester le Blacklist-System."""

import sys
import os

# Ajouter le dossier fh-swifty-chatbot au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'fh-swifty-chatbot'))

from helpers.check_blacklist import check_blacklist
import json

def test_simple():
    """Test simple avec quelques exemples."""
    print("=" * 80)
    print("🧪 EINFACHER TEST DES BLACKLIST-SYSTEMS")
    print("=" * 80)
    
    tests = [
        ("Wie kann ich mich bewerben?", "valid"),
        ("Diese FH ist Scheiße!", "not_valid"),
        ("Wie wird das Wetter?", "neutral"),
    ]
    
    for prompt, expected in tests:
        print(f"\n📝 Test: '{prompt}'")
        result = check_blacklist(prompt)
        print(f"✅ Kategorie: {result['category']}")
        print(f"💭 Grund: {result['reason']}")
        
        if result['category'] == expected:
            print("✓ KORREKT")
        else:
            print(f"✗ FEHLER (Erwartet: {expected})")
    
    print("\n" + "=" * 80)
    print("✅ Test abgeschlossen!")
    print("=" * 80)

def test_interactive():
    """Interaktiver Test-Modus."""
    print("\n" + "=" * 80)
    print("🎮 INTERAKTIVER TEST-MODUS")
    print("=" * 80)
    print("Geben Sie eine Frage ein (oder 'exit' zum Beenden):\n")
    
    while True:
        try:
            prompt = input(">>> ").strip()
            
            if not prompt:
                continue
            
            if prompt.lower() in ['exit', 'quit', 'q']:
                print("\n👋 Auf Wiedersehen!")
                break
            
            result = check_blacklist(prompt)
            
            # Farbe je nach Kategorie
            category = result['category']
            if category == 'valid':
                icon = '✅'
            elif category == 'not_valid':
                icon = '❌'
            elif category == 'neutral':
                icon = '➖'
            else:
                icon = '⚠️'
            
            print(f"\n{icon} Kategorie: {category.upper()}")
            print(f"💭 Grund: {result['reason']}\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 Auf Wiedersehen!")
            break
        except Exception as e:
            print(f"\n❌ Fehler: {str(e)}\n")

if __name__ == "__main__":
    import sys
    
    # Prüfen ob interaktiver Modus gewünscht
    if len(sys.argv) > 1 and sys.argv[1] in ['-i', '--interactive']:
        test_interactive()
    else:
        test_simple()
        print("\n💡 Tipp: Verwenden Sie 'python test_blacklist.py -i' für den interaktiven Modus")

