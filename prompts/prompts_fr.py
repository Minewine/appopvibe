"""
French prompts for CV Analyzer
"""

FULL_ANALYSIS_PROMPT_TEMPLATE_FR = """
Vous êtes un recruteur technique senior. Analysez le CV suivant par rapport à la description de poste fournie.

CV :
```
{cv}
```

Description du poste :
```
{jd}
```

**Instructions :**
Fournissez votre analyse en Markdown clair en utilisant la structure et les titres de section suivants. Soyez direct, concis et fournissez des conseils exploitables.

---

## 1. Score de Correspondance Global
- Donnez un score en pourcentage (0–100 %) indiquant dans quelle mesure le CV correspond aux exigences du poste, avec une justification brève (2–3 phrases).

## 2. Analyse des Mots-clés
- **Mots-clés Correspondants :** Listez les compétences, technologies ou qualifications de la description de poste présentes dans le CV.
- **Mots-clés Manquants :** Listez les mots-clés ou exigences importants de la description de poste absents du CV.

## 3. Analyse des Écarts de Compétences
- Identifiez les compétences, expériences ou qualifications requises par le poste mais absentes ou faibles dans le CV.

## 4. Suggestions par Section
- **Résumé/Profil :** Suggérez des améliorations pour la section résumé/profil.
- **Expérience :** Recommandez des reformulations ou ajouts pour mieux correspondre au poste.
- **Compétences :** Conseillez sur les ajouts ou modifications à la section compétences.
- **Formation/Autre :** Suggérez toute amélioration pertinente pour la formation ou d'autres sections.

## 5. Points Forts
- Résumez les principaux atouts du candidat pour ce poste.

## 6. Points Faibles et Axes d'Amélioration
- Résumez les principales faiblesses ou axes d'amélioration, au-delà des mots-clés manquants.

---

**Formatage :**
- Utilisez des listes à puces si nécessaire.
- Gardez chaque section concise et orientée action.
"""

CV_REWRITE_PROMPT_TEMPLATE_FR = """
Vous êtes un recruteur technique senior et expert en optimisation de CV. Réécrivez le CV suivant pour maximiser sa correspondance avec la description de poste et améliorer ses chances de passer les systèmes de suivi des candidatures (ATS).

CV :
```
{cv}
```

Description du poste :
```
{jd}
```

**Instructions :**
Réécrivez le CV en Markdown professionnel en suivant ces consignes :

1. Intégrez les mots-clés et compétences pertinents de la description de poste dans tout le CV.
2. Mettez en avant les compétences transférables et les expériences directement pertinentes.
3. Utilisez des réalisations quantifiables et des exemples précis si possible.
4. Organisez le CV avec des titres de section clairs : Résumé/Profil, Expérience, Compétences, Formation, Autre (si applicable).
5. Préservez toutes les informations importantes du CV original, mais reformulez et réorganisez pour plus de clarté et d'impact.
6. Assurez-vous que le CV est honnête, concis et adapté à la description de poste.
7. Formatez le CV pour la compatibilité ATS (évitez les tableaux, images ou formatages inhabituels).

---

**Format de sortie :**
- Utilisez le Markdown avec des titres de section clairs.
- Utilisez des listes à puces pour les réalisations et compétences.
- Gardez un ton direct et professionnel.
"""
