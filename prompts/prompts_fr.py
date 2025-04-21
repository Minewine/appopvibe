"""
French prompts for CV Analyzer
"""

FULL_ANALYSIS_PROMPT_TEMPLATE_FR = """
J'ai besoin que vous analysiez un CV par rapport à une description de poste.

CV:
```
{cv}
```

Description du poste:
```
{jd}
```

Veuillez fournir une analyse complète au format Markdown avec les sections distinctes suivantes :

### Score de Correspondance Global
- Fournissez un score en pourcentage (0-100%) indiquant dans quelle mesure le CV correspond aux exigences de la description de poste. Justifiez brièvement le score.

### Analyse des Mots-clés
- **Mots-clés Correspondants :** Listez les compétences clés, technologies ou qualifications de la description de poste trouvées dans le CV.
- **Mots-clés Manquants :** Listez les mots-clés importants de la description de poste *non* trouvés dans le CV.

### Analyse des Écarts de Compétences
- Identifiez les domaines de compétences ou d'expérience spécifiques mentionnés dans la description de poste où le candidat semble manquer d'expérience d'après le CV.

### Suggestions par Section
- **Résumé/Profil :** Fournissez des suggestions spécifiques pour améliorer la section résumé du CV pour ce poste.
- **Expérience :** Suggérez des améliorations ou des façons de reformuler les points d'expérience pour mieux correspondre à la description du poste.
- **Compétences :** Recommandez des ajouts ou des modifications à la section compétences.
- **Formation/Autre :** Notez toute suggestion pertinente pour les autres sections du CV.

### Points Forts
- Résumez les principaux points forts du profil du candidat pour ce rôle spécifique.

### Points Faibles/Axes d'Amélioration
- Résumez les principaux points faibles ou les domaines où le CV pourrait être considérablement amélioré pour ce rôle, au-delà de l'ajout de mots-clés.

Soyez direct, concis et fournissez des conseils exploitables sous chaque section.
"""

CV_REWRITE_PROMPT_TEMPLATE_FR = """
J'ai besoin que vous réécriviez le CV suivant pour l'optimiser pour les ATS (systèmes de suivi des candidats) en fonction de cette description de poste.

CV:
```
{cv}
```

Description du poste:
```
{jd}
```

Veuillez réécrire le CV au format Markdown pour:
1. Incorporer les mots-clés pertinents de la description du poste.
2. Mettre en évidence les compétences transférables et les expériences pertinentes.
3. Utiliser des réalisations quantifiables lorsque c'est possible.
4. Maintenir une structure propre et professionnelle avec des titres de section clairs.
5. S'assurer que toutes les informations importantes du CV original sont préservées.
6. Se concentrer sur la réussite des filtres ATS tout en restant honnête.

Formatez le CV en Markdown propre avec des titres appropriés pour chaque section.
"""
