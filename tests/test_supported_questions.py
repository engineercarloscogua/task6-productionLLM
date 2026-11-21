from src.guardrails import classify_scope
from src.pdf_knowledge import pdf_knowledge_store


SUPPORTED_QUESTIONS = [
    "¿Qué es Renta Joven y para qué sirve?",
    "¿Yo puedo inscribirme a Renta Joven si apenas estoy en primer semestre?",
    "¿Qué requisitos tengo que cumplir para entrar a Renta Joven?",
    "¿Qué edad debo tener para participar en el programa?",
    "¿Necesito estar registrado en el Sisbén para recibir el beneficio?",
    "¿Qué grupos del Sisbén pueden aplicar a Renta Joven?",
    "¿Si no tengo Sisbén, puedo inscribirme?",
    "¿Cómo hago para saber si estoy registrado en Renta Joven?",
    "¿Dónde puedo hacer la inscripción?",
    "¿Cuándo vuelven a abrir inscripciones para Renta Joven?",
    "¿Si estudio en Unitrópico, puedo recibir Renta Joven?",
    "¿Qué documentos necesito para inscribirme?",
    "¿Cuánto dinero entrega Renta Joven a los estudiantes universitarios?",
    "¿Cada cuánto pagan Renta Joven?",
    "¿Cómo puedo saber cuándo me van a pagar?",
    "¿El dinero me lo consignan a una cuenta bancaria?",
    "¿Puedo recibir el beneficio si todavía no tengo una cuenta bancaria?",
    "¿El programa me ayuda a pagar la matrícula o es para mis gastos personales?",
    "¿Qué pasa si no recibo el pago que me corresponde?",
    "¿Tengo que sacar buenas notas para que me paguen?",
    "¿Qué pasa si pierdo una materia?",
    "¿Si cancelo el semestre, pierdo Renta Joven?",
    "¿Puedo seguir recibiendo el beneficio durante toda mi carrera?",
    "¿Si me cambio de carrera, puedo continuar en Renta Joven?",
    "¿Tengo que realizar actividades de voluntariado para recibir el apoyo?",
    "¿Renta Joven también ofrece cursos o capacitaciones?",
    "¿Qué beneficios tiene Renta Joven aparte del dinero?",
    "¿Qué pasa cuando me gradúe de la universidad?",
    "¿Qué es el programa Bien-Estar Contigo?",
    "¿Qué ayudas ofrece Bien-Estar Contigo a los estudiantes?",
    "¿Si soy estudiante de primer semestre, puedo solicitar el apoyo de alimentación?",
    "¿Cómo hago para inscribirme al apoyo de alimentación?",
    "¿Cuándo abren las inscripciones para Bien-Estar Contigo?",
    "¿Qué documentos tengo que presentar para solicitar el beneficio?",
    "¿Necesito tener Sisbén para poder participar?",
    "¿Qué grupos del Sisbén tienen prioridad?",
    "¿Si soy víctima del conflicto armado, tengo prioridad?",
    "¿Si pertenezco a una comunidad indígena, puedo recibir el beneficio?",
    "¿Necesito tener un promedio mínimo para inscribirme?",
    "¿Si soy de primer semestre y todavía no tengo notas, cómo hago para cumplir el requisito del promedio?",
    "¿Cuántas materias o créditos debo tener matriculados?",
    "¿Necesito tener el carné estudiantil para inscribirme?",
    "¿Cuánto dinero entrega Bien-Estar Contigo?",
    "¿El beneficio lo entregan en dinero o en bonos de mercado?",
    "¿En qué supermercados puedo utilizar los bonos?",
    "¿Durante cuántos meses entregan el apoyo de alimentación?",
    "¿Me consignan el dinero directamente a mi cuenta bancaria?",
    "¿Cuántos estudiantes pueden recibir el apoyo?",
    "¿El beneficio cubre todos los gastos de alimentación del semestre?",
    "¿Cómo puedo saber si fui seleccionado?",
    "¿Qué pasa si hay más estudiantes inscritos que cupos disponibles?",
    "¿Cómo deciden quiénes reciben el beneficio?",
    "¿Qué puedo hacer si no aparezco en la lista de beneficiarios?",
    "¿Dónde puedo presentar una reclamación?",
    "¿Si pierdo materias, me pueden quitar el apoyo?",
    "¿Tengo que participar en actividades de Bienestar Universitario?",
    "¿Puedo volver a inscribirme el próximo semestre?",
    "¿Si ya recibí el beneficio una vez, tengo prioridad para volver a recibirlo?",
    "¿Qué pasa si no entrego los documentos en las fechas establecidas?",
    "¿A qué oficina de Unitrópico puedo acudir si tengo problemas con mi inscripción?",
    "¿Cuál es la diferencia entre Renta Joven y Bien-Estar Contigo?",
    "¿Puedo inscribirme a Renta Joven y a Bien-Estar Contigo al mismo tiempo?",
    "¿Si recibo Renta Joven, también puedo recibir el bono de alimentación de Unitrópico?",
    "¿Cuál de los dos programas me conviene más si apenas estoy empezando la universidad?",
    "¿Cuál de los dos programas entrega más dinero?",
    "¿Los dos programas exigen tener Sisbén?",
    "¿Si no cumplo los requisitos de Renta Joven, puedo solicitar Bien-Estar Contigo?",
    "¿Tengo que mantener buenas calificaciones para conservar cualquiera de los dos apoyos?",
    "¿Qué programa me puede ayudar con mis gastos mientras estudio?",
    "¿Dónde puedo preguntar en Unitrópico cuál de los dos programas puedo solicitar?",
]


def test_all_supported_questions_pass_the_local_scope_filter() -> None:
    rejected = [
        (question, classify_scope(question).reason)
        for question in SUPPORTED_QUESTIONS
        if not classify_scope(question).allowed
    ]

    assert rejected == []


def test_all_supported_questions_retrieve_document_sources() -> None:
    pdf_knowledge_store.refresh(force=True)
    without_sources = [
        question
        for question in SUPPORTED_QUESTIONS
        if "Fuente:" not in pdf_knowledge_store.context(question, k=3)
    ]

    assert without_sources == []
