"""
Main routes for the CV Analyzer application.
"""
import os
import logging
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, current_app, abort, session
)

from appopvibe.models import CVAnalysisForm
from appopvibe.services import AnalyzerService, ReportService

# Create blueprint
main_bp = Blueprint('main', __name__)

# Setup logger
logger = logging.getLogger(__name__)

@main_bp.route('/', methods=['GET'])
def index():
    """Render the landing page."""
    return render_template('landing.html')

@main_bp.route('/form', methods=['GET'])
def submit_cv():
    """Render the CV analysis form with default values from config."""
    # Import from root config.py file, not from appopvibe.config
    from config import default_cv, default_jd
    
    form = CVAnalysisForm()
    
    # Only pre-populate if form is not already populated
    if not form.cv.data:
        form.cv.data = default_cv
    if not form.jd.data:
        form.jd.data = default_jd
        
    return render_template('form.html', form=form)

@main_bp.route('/analyze', methods=['POST'])
async def analyze():
    """Process the CV and job description for analysis."""
    form = CVAnalysisForm()
    
    if not form.validate_on_submit():
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {field}: {error}", "error")
        return redirect(url_for('main.index'))
    
    try:
        # Get form data
        cv_text = form.cv.data
        jd_text = form.jd.data
        language = form.language.data
        rewrite_cv = form.rewrite_cv.data
        
        # Log submission
        logger.info(f"Processing submission - Language: {language}, Rewrite CV: {rewrite_cv}")
        
        # Create required services
        from appopvibe.services import LLMService
        from appopvibe.services.llm.llm_service import LLMProvider
        import os
        from flask import current_app
        
        # Define default templates since PROMPT_TEMPLATES is not in config
        DEFAULT_TEMPLATES = {
        'en': {
            'analysis': """
You are a senior technical recruiter. Analyze the following CV against the provided job description.

CV:
{cv}

Job Description:
{jd}

**Instructions:**
1. Your **SOLE TASK** is to perform the analysis and output it in the specified Markdown format.
2. **ABSOLUTELY NO** conversational text, introductions, or explanations before or after the analysis output.
3. **ABSOLUTELY NO** JSON, dictionary structures, code blocks, or any other wrapping around the analysis content.
4. **ABSOLUTELY DO NOT** include the original CV or Job Description in the output.
5. **ABSOLUTELY DO NOT** generate a rewritten version of the CV.
6. Produce your analysis strictly using the Markdown structure provided in the "OUTPUT STRUCTURE" section below.

---
**OUTPUT STRUCTURE:**
(Your output MUST begin EXACTLY with the first required Markdown heading: '## 1. Overall Match Score'. There should be NOTHING before it.)

## 1. Overall Match Score
- Give a percentage score (0–100%) for how well the CV matches the job requirements.
- Briefly justify your score in 2–3 sentences.

## 2. Keyword Analysis
- **Matched Keywords:** List key skills, technologies, or qualifications *verbatim* from the job description that are clearly present in the CV.
- **Missing Keywords:** List important keywords or requirements *verbatim* from the job description that are NOT found in the CV.

## 3. Skill Gap Analysis
- Identify specific skills, experiences, or qualifications required by the job but missing or weak in the CV, based on the job description, beyond just individual keywords.

## 4. Section-by-Section Suggestions
- Provide specific, actionable suggestions for improving *each* of the following CV sections to better match the job. Suggest how content could be rephrased or what type of relevant information should be added based on the job description requirements:
    - **Summary/Profile:** Suggestions for this section.
    - **Experience:** Recommendations for improving bullet points.
    - **Skills:** Advice on additions or changes.
    - **Education/Other:** Suggest any relevant improvements for education or other sections.

## 5. Strengths
- Summarize the main strengths of the candidate *specifically* for this role, based on the job description.

## 6. Weaknesses & Improvement Areas
- Summarize the main weaknesses or areas for improvement, based on the job description, going beyond just missing keywords.

---
**Formatting Guidelines within Sections:**
- Use Markdown bullet points (`-`) where appropriate.
- Keep language direct and professional.
- Adhere strictly to the section headings and numbering provided above.
""",
            'rewrite': """
You are a senior technical recruiter and expert in resume optimization. Rewrite the following CV to maximize its match with the provided job description and improve its chances of passing Applicant Tracking Systems (ATS).

CV:
{cv}

Job Description:
{jd}

**Output Instructions:**
1. Your *entire* output *must* be the rewritten CV in clear, professional Markdown format.
2. **ABSOLUTELY DO NOT** include any introductory text, explanations, conversational filler, or surrounding formatting like JSON, code blocks, or dictionary structures.
3. **ABSOLUTELY DO NOT** generate an analysis of the CV or job description. Your *sole task* is rewriting.
4. Incorporate relevant keywords and skills from the job description throughout the CV where appropriate and truthful.
5. Emphasize transferable skills and directly relevant experiences for the target role.
6. Use quantifiable achievements and specific examples from the original CV or implied by experience where possible.
7. Preserve all important and truthful information from the original CV, but rephrase and reorganize as needed for clarity, impact, and relevance to the job description.
8. Structure the rewritten CV *strictly* using the following section headings *in this order*. Only include a section if there is relevant content from the original CV to place under it:
    - Summary/Profile
    - Experience
    - Projects (if applicable, based on original CV)
    - Skills
    - Education
    - Other (if applicable, based on original CV)
9. Format the CV for ATS compatibility using standard Markdown: use clear headings (`##`), bullet points (`-`), and plain text. Avoid tables, images, or unusual formatting.
10. Keep language direct and professional.

---

**Output Format Example (Your output should begin directly with the first section heading):**

## Summary/Profile
[Optimized summary here]

## Experience
[Optimized experience bullet points here]

## Projects
[Optimized project details here, if applicable and separate from experience]

## Skills
[Optimized skills list here]

## Education
[Optimized education details here]

## Other
[Any other relevant optimized information here, if applicable]
"""
        },
        'fr': {
            'analysis': """
Vous êtes un recruteur technique senior. Analysez le CV suivant par rapport à la description de poste fournie.

CV:
{cv}

DESCRIPTION DU POSTE:
{jd}

**Instructions:**
1. Votre **SEULE TÂCHE** est d'effectuer l'analyse et de la produire au format Markdown spécifié.
2. **ABSOLUMENT AUCUN** texte conversationnel, introduction ou explication avant ou après la sortie de l'analyse.
3. **ABSOLUTEMENT AUCUNE** structure JSON, dictionnaire, blocs de code, ou tout autre enveloppement autour du contenu de l'analyse.
4. **NE PAS ABSOLUMENT** inclure le CV original ou la description de poste dans la sortie.
5. **NE PAS ABSOLUMENT** générer une version réécrite du CV.
6. Produisez votre analyse en utilisant strictement la structure Markdown fournie dans la section "STRUCTURE DE SORTIE" ci-dessous.

---
**STRUCTURE DE SORTIE:**
(Votre sortie DOIT commencer EXACTEMENT par le premier titre Markdown requis : '## 1. Score de correspondance global'. Il ne doit y avoir RIEN avant.)

## 1. Score de correspondance global
- Donnez un score en pourcentage (0–100%) pour l'adéquation du CV avec les exigences du poste.
- Justifiez brièvement votre score en 2 à 3 phrases.

## 2. Analyse des mots-clés
- **Mots-clés correspondants :** Listez les compétences clés, technologies ou qualifications *telles qu'elles apparaissent textuellement* dans la description de poste et qui sont clairement présentes dans le CV.
- **Mots-clés manquants :** Listez les mots-clés ou exigences importants *tels qu'ils apparaissent textuellement* dans la description de poste et qui ne sont PAS trouvés dans le CV.

## 3. Analyse des écarts de compétences
- Identifiez les compétences, expériences ou qualifications spécifiques requises par le poste mais manquantes ou faibles dans le CV, sur la base de la description de poste, au-delà des simples mots-clés individuels.

## 4. Suggestions section par section
- Fournissez des suggestions spécifiques et exploitables pour améliorer *chacune* des sections suivantes du CV afin de mieux correspondre au poste. Suggérez comment le contenu pourrait être reformulé ou quel type d'informations pertinentes devrait être ajouté en fonction des exigences de la description de poste :
    - **Résumé/Profil :** Suggestions pour cette section.
    - **Expérience :** Recommandations pour améliorer les points de liste d'expérience.
    - **Compétences :** Conseils sur les ajouts ou les modifications.
    - **Formation/Autre :** Suggérez toute amélioration pertinente pour la formation ou d'autres sections.

## 5. Points forts
- Résumez les principaux points forts du candidat *spécifiquement* pour ce rôle, sur la base de la description de poste.

## 6. Faiblesses et domaines d'amélioration
- Résumez les principales faiblesses ou domaines d'amélioration, sur la base de la description de poste, allant au-delà des simples mots-clés manquants.

---
**Directives de formatage dans les sections :**
- Utilisez des points de liste Markdown (`-`) le cas échéant.
- Gardez un langage direct et professionnel.
- Adhérez strictement aux titres de section et à la numérotation fournis ci-dessus.
""",
            'rewrite': """
Vous êtes un recruteur technique senior et un expert en optimisation de CV. Réécrivez le CV suivant pour maximiser sa correspondance avec la description de poste fournie et améliorer ses chances de passer les systèmes de suivi des candidatures (ATS).

CV:
{cv}

DESCRIPTION DU POSTE:
{jd}

**Instructions de sortie :**
1. Votre *sortie entière* DOIT être le CV réécrit au format Markdown clair et professionnel.
2. **ABSOLUMENT AUCUN** texte d'introduction, explication, remplissage conversationnel, ou formatage environnant comme JSON, blocs de code, ou structures de dictionnaire.
3. **NE PAS ABSOLUMENT** générer une analyse du CV ou de la description de poste. Votre *seule tâche* est la réécriture.
4. Intégrez les mots-clés et compétences pertinents de la description de poste tout au long du CV là où c'est approprié et véridique.
5. Mettez l'accent sur les compétences transférables et les expériences directement pertinentes pour le rôle ciblé.
6. Utilisez des réalisations quantifiables et des exemples spécifiques du CV original ou implicites par l'expérience si possible.
7. Conservez toutes les informations importantes et véridiques du CV original, mais reformulez et réorganisez-les si nécessaire pour plus de clarté, d'impact et de pertinence par rapport à la description de poste.
8. Structurez le CV réécrit *strictement* en utilisant les titres de section suivants *dans cet ordre*. N'incluez une section que si le CV original contient du contenu pertinent à y placer :
    - Résumé/Profil
    - Expérience
    - Projets (si applicable, basé sur le CV original)
    - Compétences
    - Formation
    - Autre (si applicable, basé sur le CV original)
9. Formatez le CV pour la compatibilité ATS en utilisant Markdown standard : utilisez des titres clairs (`##`), des points de liste (`-`), et du texte brut. Évitez les tableaux, les images ou les formats inhabituels.
10. Gardez un langage direct et professionnel.

---

**Exemple de format de sortie (Votre sortie doit commencer directement par le premier titre de section) :**

## Résumé/Profil
[Résumé optimisé ici]

## Expérience
[Points de liste d'expérience optimisés ici]

## Projets
[Détails de projets optimisés ici, si applicable et séparé de l'expérience]

## Compétences
[Liste de compétences optimisée ici]

## Formation
[Détails de formation optimisés ici]

## Autre
[Toute autre information pertinente optimisée ici, si applicable]
"""
        }
    }


        # Set up directories
        reports_dir = current_app.config.get('REPORTS_FOLDER', os.path.join(os.getcwd(), 'reports'))
        os.makedirs(reports_dir, exist_ok=True)
        
        # Initialize services with required dependencies and explicitly set API key
        # Get API keys directly from environment
        groq_api_key = os.getenv('GROQ_API_KEY')
        
        if not groq_api_key:
            logger.error("No GROQ_API_KEY found in environment variables")
            raise ValueError("Missing GROQ_API_KEY environment variable")
            
        # Initialize LLM service with explicit API key and provider
        llm_service = LLMService(
            api_key=groq_api_key,
            provider="groq",
            default_model="llama-3.3-70b-versatile"
        )
        
        logger.info(f"Using {llm_service.provider} as LLM provider with model {llm_service.default_model}")
        
        analyzer_service = AnalyzerService(llm_service, DEFAULT_TEMPLATES)
        report_service = ReportService(reports_directory=reports_dir)
        
        # Analyze CV and job description
        result = await analyzer_service.process_submission(
            cv_text, jd_text, language, rewrite_cv
        )

        # Correctly extract analysis and rewrite results from the dictionary
        analysis_result = result.get('analysis', '') # Get the analysis string
        rewrite_result = result.get('rewritten_cv') # Get the rewritten_cv string (can be None)

        # Save results to a report file
        report_filename = report_service.save_report(
            cv_text, jd_text, analysis_result, # Pass the analysis string
            rewrite_result, # Pass the rewrite string (or None)
            language
        )

        # Save report ID in session for security
        session['current_report_id'] = report_filename
        
        # Redirect to the report view
        return redirect(url_for('report.view_report', report_id=report_filename))
    
    except Exception as e:
        logger.exception(f"Error processing submission: {e}")
        flash("An error occurred while analyzing your CV. Please try again.", "error")
        return redirect(url_for('main.index'))

@main_bp.route('/feedback', methods=['GET', 'POST'])
@main_bp.route('/feedback/', methods=['GET', 'POST'])
def feedback():
    """Handle feedback form submission."""
    if request.method == 'POST':
        # Process the feedback submission (you can add more processing code here)
        flash('Thank you for your feedback!', 'success')
        # Redirect back to the landing page instead of staying on feedback
        return redirect(url_for('main.index'))
    
    # For GET requests, redirect to the landing page with a fragment to scroll to the feedback section
    return redirect(url_for('main.index') + '#feedback')
