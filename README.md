# Niplan Market 🚀 | Business Builder for WhatsApp Economy

**Niplan Market** est une plateforme SaaS "Multi-tenant" conçue pour digitaliser l'économie informelle en République Démocratique du Congo. Elle permet aux vendeurs locaux de transformer leurs status WhatsApp en véritables boutiques en ligne professionnelles en moins de 2 minutes.

![Status to Store](https://via.placeholder.com/800x400?text=From+WhatsApp+Status+to+Online+Store)

## 🌟 Pourquoi Niplan Market ?

En RDC, la majorité du commerce se fait via WhatsApp. Cependant, les vendeurs font face à trois problèmes :

1. **Éphémérité :** Les status disparaissent après 24h.
2. **Friction :** Répéter les prix et détails manuellement à chaque client est épuisant.
3. **Visibilité :** Les produits ne sont pas indexés sur Google.

**Niplan Market** résout cela en offrant un catalogue permanent, optimisé pour mobile et intégré à WhatsApp.

## 🛠️ Stack Technique

- **Backend :** Django 5.0 (Python) & Django Rest Framework (DRF)
- **Frontend :** React.js & Tailwind CSS
- **Base de données :** PostgreSQL
- **Stockage Images :** Cloudinary (Optimisation automatique pour connexions lentes)
- **Authentification :** JWT & OTP Passwordless via WhatsApp
- **Infrastructure :** Docker & Docker-Compose
- **Déploiement :** Railway (API) & Vercel (Frontend)
- **CI/CD :** GitHub Actions

## ✨ Fonctionnalités clés (MVP)

- [x] **Connexion Passwordless :** Authentification par numéro de téléphone via OTP WhatsApp.
- [x] **Création Auto :** Un Business et un catalogue sont générés instantanément après l'inscription.
- [x] **Mobile-First Upload :** Prise de photo directe depuis le téléphone pour ajouter un produit (Style Status).
- [x] **WhatsApp Order :** Bouton de commande qui ouvre une discussion pré-remplie avec le vendeur.
- [x] **Optimisation Data :** Compression automatique des images pour économiser les forfaits internet (Megalots).

## 🚀 Installation & Lancement

### Avec Docker (Recommandé)

1. Clonez le projet :
   ```bash
   git clone [https://github.com/Siri6k/backend-niplan.git](https://github.com/Siri6k/backend-niplan.git)

   ```
