# sarf.py
import re
import stanza
from camel_tools.tokenizers.word import simple_word_tokenize
from camel_tools.disambig.mle import MLEDisambiguator
from camel_tools.morphology.database import MorphologyDB
from camel_tools.morphology.analyzer import Analyzer

# ——— Model setup ———
# (Run once: stanza.download('ar'))
disambig  = MLEDisambiguator.pretrained()
morph_db  = MorphologyDB.builtin_db()
analyzer  = Analyzer(morph_db)
nlp        = stanza.Pipeline(
    lang="ar", 
    processors="tokenize,mwt,pos,lemma,depparse", 
    use_gpu=False
)

# ——— Globals ———
# ——— Globals ———
TOOLS = {
    "في","من","إلى","عن","على","مع","حتى","رب","مذ","فـ","ثم",
    "أو","أم","بل","لا","لكن","لم","لن",        
    "ليس","إنْ","لما","أن","إذن","كي","إذا","لو",
    "لولا","كلما","أين","أي","أنى","أيا","هيا",
    "متى","كيف","كم","لماذا","ماذا","سوف"
}

NOUN_POS         = {"noun","noun_prop"}
DISJ_PRON        = {"أنا","أنتَ","أنتِ","هو","هي","نحن","أنتما","أنتن","هما","هم","هن"}
DEMOS            = {"هذا","هذه","هذان","هاتان","هؤلاء","ذلك","تلك","ذانك","تانك","أولئك"}
PRESENT_PREFIXES = ("ي","ت")
NEG              = {"لم","لن","لا"}
QUESTION         = {"هل"}
TIME_WORDS       = {"غدا","غداً","مساء","صباح","صباحا","ليلا","ليلاً","اليوم"}
PLACE_WORDS      = {"أرض","أرضا","ساحة","ساحةً","حديقة","حديقةً","شارع","شارعاً","غابة","غابةً",}


# ——— Helpers ———
def is_past_verb(word: str) -> bool:
    for a in analyzer.analyze(word):
        if a.get('pos')=='verb' and a.get('aspect')=='perf':
            return True
    return False

def is_adj_or_part(word: str) -> bool:
    for a in analyzer.analyze(word):
        if a.get('pos') in ('adj','part'):
            return True
    return False

def is_adv(word: str) -> bool:
    for a in analyzer.analyze(word):
        if a.get('pos') == 'adv':
            return True
    return False

# ——— Main ———
def analyze_sentence(sentence: str) -> str:
    # 0) normalize
    s = re.sub(r'[\u064B-\u0652]', '', sentence)
    s = s.replace('\u0640','')
    tokens = simple_word_tokenize(s)
    n = len(tokens)

    # unpack for 2- and 3-word rules
    if n == 2:
        w1, w2 = tokens
    if n == 3:
        w1, w2, w3 = tokens

        # 1) length & tool-word filter
    if n < 2 or n > 3:
            return "❗ يجب أن تكون الجملة مكوّنة من كلمتين أو ثلاث."
    # only block “tool words” for 2-word inputs
    if n == 2 and (any(ch.isascii() for ch in "".join(tokens))
        or any(t in TOOLS for t in tokens)):
     return "هذه ليست جملة تامة."


    # 2) morphological analyses
    disams = disambig.disambiguate(tokens)
    pos    = [d.analyses[0].analysis.get("pos","").lower()    for d in disams]
    asp    = [d.analyses[0].analysis.get("aspect","")         for d in disams]
    case   = [d.analyses[0].analysis.get("case","")           for d in disams]
    mood   = [d.analyses[0].analysis.get("mood","")           for d in disams]

    # 3) UD parse + fallback
    doc      = nlp(s)
    ud_words = [w for w in doc.sentences[0].words if w.upos!="PUNCT"]
    if len(ud_words) < n:
        return "تعذر التحليل."
    upos_list, dep_list = [], []
    for i, w in enumerate(ud_words):
        u_p, u_d = w.upos, w.deprel
        if u_p=="X":    u_p = pos[i].upper()
        if u_d=="nmod": u_d = "nsubj" if case[i]=="nom" else "obj"
        if u_d=="obl":  u_d = "obj"
        upos_list.append(u_p)
        dep_list.append(u_d)


    # DEBUG: dump all key features for the first two tokens
    print("DEBUG TOKENS:", tokens)
    print(" DEBUG pos  :", pos)
    print(" DEBUG aspect:", asp)
    print(" DEBUG case :", case)
    print(" DEBUG mood :", [d.analyses[0].analysis.get("mood","") for d in disams])
    print(" DEBUG UPOS :", upos_list)
    print(" DEBUG DEPREL:", dep_list)

    def is_past_verb(word: str) -> bool:
        for a in analyzer.analyze(word):
            if a.get('pos') == 'verb' and a.get('asp') == 'perf':
                return True
        return False

    # ——— 2-word rules ———

    # Rule 1: اسم + فعل (فاعل متقدم)
    if n==2 and pos[0] in NOUN_POS and upos_list[1]=="VERB":
        subj     = w1 + "ُ"
        verb_tok = w2
        verb     = verb_tok + "َ"
        note     = ""
        if verb_tok.endswith("تْ"):
            note = "، والتاء تأنيث ساكنة لا محل لها من الإعراب"
        return f"""نوع الجملة: اسمية (فاعل متقدم)
{subj}: فاعل مرفوع، وعلامة رفعه الضمة الظاهرة على آخره.
{verb}: فعل ماضٍ مبنيّ على الفتح الظاهر على آخره{note}."""

    # Rule 2: فعل + ظرف زمان/مكان
    if n == 2 and upos_list[0] == "VERB" and (
        upos_list[1] == "ADV"
        or w2 in TIME_WORDS
    ):
        return f"""نوع الجملة: فعلية
{w1}: فعل ماضٍ مبنيّ على الفتح الظاهر على آخره.
{w2}: ظرف منصوب، وعلامة نصبه الفتحة الظاهرة على آخره."""

       # grab all Camel Analyzer analyses for the verb
    analyses1 = analyzer.analyze(w1)
    is_verb1  = any(a.get('pos') == 'verb' for a in analyses1)
    is_imp    = any(a.get('asp') == 'imp' for a in analyses1)
    is_pres   = w1.startswith(PRESENT_PREFIXES) and is_verb1
    # note: anything verb-like that’s not present or imperative we’ll treat as past

    # Rule 3: فعل ماضٍ + مفعول به
    if n == 2 and is_verb1 and not is_pres and not is_imp and dep_list[1] == "obj":
        verb_past = w1 + "َ"   # fatha on the past verb
        obj_acc   = w2 + "َ"   # fatha on the object
        return f"""نوع الجملة: فعلية
{verb_past}: فعل ماضٍ مبنيّ على الفتح الظاهر على آخره.
{obj_acc}: مفعول به منصوب، وعلامة نصبه الفتحة الظاهرة."""

    # Rule 4: فعل مضارع + مفعول به (فاعل مستتر)
    if n == 2 and w1.startswith(PRESENT_PREFIXES) \
        and upos_list[0] == "VERB" and upos_list[1] == "NOUN":
        obj_acc = w2 + "َ"
        return f"""نوع الجملة: فعلية
{w1}: فعل مضارع مرفوع، وعلامة رفعه الضمة الظاهرة.
{obj_acc}: مفعول به منصوب، وعلامة نصبه الفتحة الظاهرة."""

    # Rule 5: ظرف مكان + خبر (وجودية)
    if n==2 and upos_list[0]=="ADV" and pos[1] in NOUN_POS:
        return f"""نوع الجملة: اسمية وجودية
{w1}: ظرف مبني في محل رفع مبتدأ.
{w2}: خبر مرفوع، وعلامة رفعه الضمة الظاهرة على آخره."""

    # Rule 6: حرف استفهام + فعل
    if n==2 and w1 in QUESTION and upos_list[1]=="VERB":
        return f"""نوع الجملة: استفهامية
{w1}: حرف استفهام لا محل له من الإعراب.
{w2}: فعل ماضٍ مبني على الفتح الظاهر على آخره."""

    # Rule 7: أداة نداء + منادى
    if n==2 and w1=="يا" and pos[1] in NOUN_POS:
        munda = w2 + "َ"
        return f"""نوع الجملة: نداءية
{w1}: أداة نداء مبنية لا محل لها من الإعراب.
{munda}: منادى منصوب، وعلامة نصبه الفتحة الظاهرة على آخره."""

    # Rule 8: أداة تعجب + فعل جامد (جملة تعجبية)
    if n == 2 and w1 == "ما" and upos_list[1] in ("VERB", "ADJ"):
        verb_form = w2 + "َ"
        return f"""نوع الجملة: تعجبية
{w1}: ما التعجبية، مبتدأ مرفوع.
{verb_form}: فعل ماضٍ جامد مبنيّ على الفتح الظاهر على آخره، والفاعل ضمير مستتر."""

        # — 3-word rules ——

    # Rule A: اسم + خبر + نعت (ADJ + ADJ)
    if n == 3 and upos_list[0]=="NOUN" and upos_list[1]=="ADJ" and upos_list[2]=="ADJ":
        subj = w1 + "ُ"
        khbr = w2 + "ٌ"
        naat = w3 + "ٌ"
        return f"""نوع الجملة: اسمية ثلاثية (مبتدأ + خبر + نعت)
{subj}: مبتدأ مرفوع، وعلامة رفعه الضمة الظاهرة.
{khbr}: خبر مرفوع للمبتدأ، وعلامة رفعه الضمة الظاهرة.
{naat}: نعت مرفوع يتبع المبتدأ والخبر في الإعراب، وعلامة رفعه الضمة الظاهرة."""
    
     # Rule B: فعل ماضٍ + فاعل + مفعول به
    if n == 3 and is_past_verb(w1) \
           and pos[1] in NOUN_POS \
           and pos[2] in NOUN_POS \
           and w3 not in TIME_WORDS and w3 not in PLACE_WORDS:
        return f"""نوع الجملة: فعليّة ثلاثية (فعل + فاعل + مفعول به)
{w1 + 'َ'}: فعل ماضٍ مبنيّ على الفتح الظاهر على آخره.
{w2 + 'ُ'}: فاعل مرفوع، وعلامة رفعه الضمة الظاهرة.
{w3 + 'َ'}: مفعول به منصوب، وعلامة نصبه الفتحة الظاهرة."""
    

    # Rule E: فعل + فاعل + حال
    if n == 3 and upos_list[0]=="VERB" and pos[1] in NOUN_POS and upos_list[2]=="ADJ":
        verb_form = w1 + ("َ" if is_past_verb(w1) else "")
        verb_desc = ("فعل ماضٍ مبنيّ على الفتح الظاهر على آخره."
                     if is_past_verb(w1)
                     else "فعل مضارع مرفوع، وعلامة رفعه الضمة الظاهرة.")
        return f"""نوع الجملة: فعليّة ثلاثية (فعل + فاعل + حال)
{verb_form}: {verb_desc}
{w2 + 'ُ'}: فاعل مرفوع، وعلامة رفعه الضمة الظاهرة.
{w3 + 'َ'}: حال منصوب، وعلامة نصبه الفتحة الظاهرة."""
    
   
# Rule F (fallback): generic فعل + فاعل + مفعول به
# only if the third word is NOT a time‐ or place‐adverb
    if n == 3 \
        and pos[0] == "verb" \
        and pos[1] in NOUN_POS \
        and pos[2] in NOUN_POS \
        and w3 not in TIME_WORDS \
        and w3 not in PLACE_WORDS:
        verb_form = w1 + ("َ" if is_past_verb(w1) else "")
        desc = ("فعل ماضٍ مبنيّ على الفتح الظاهر على آخره."
                if is_past_verb(w1)
                else "فعل مضارع مرفوع، وعلامة رفعه الضمة الظاهرة.")
        return f"""نوع الجملة: فعليّة ثلاثية (فعل + فاعل + مفعول به)
{verb_form}: {desc}
{w2}ُ: فاعل مرفوع، وعلامة رفعه الضمة الظاهرة.
{w3}َ: مفعول به منصوب، وعلامة نصبه الفتحة الظاهرة."""

        # Rule X: نفي/جزم + فعل + نائب فاعل
    if n == 3 and w1 == "لم" \
            and w2.startswith(PRESENT_PREFIXES) and upos_list[1] == "VERB":
        # build forms with diacritics
        verb_jazm = w2 + "ْ"       # sukun on the last letter
        subj_nf   = w3 + "ُ"       # damma on the noun
        return f"""نوع الجملة: فعلية جزمية/نفي
{w1}: حرف جزم ونفي يفيد الماضي، لا محل له من الإعراب.
{verb_jazm}: فعل مضارع مجزوم بالسكون الظاهر على آخره، والفاعل ضمير مستتر.
{subj_nf}: نائب فاعل مرفوع، وعلامة رفعه الضمة الظاهرة."""

        # Rule Y: نصب المضارع + مفعول به (أداة نصب ونفي للمضارع)
    if n == 3 and w1 == "لن" \
          and w2.startswith(PRESENT_PREFIXES) and upos_list[1] == "VERB":
        # build the diacritics
        verb_nasb = w2 + "َ"    # fatha on the present verb for نصب
        obj_acc   = w3 + "َ"    # fatha on the object
        return f"""نوع الجملة: فعلية نصب مضارع
{w1}: أداة نصب ونفي للمضارع لا محل لها من الإعراب.
{verb_nasb}: فعل مضارع منصوب بالفتحة الظاهرة، والفاعل ضمير مستتر.
{obj_acc}: مفعول به منصوب، وعلامة نصبه الفتحة الظاهرة."""

     # Rule X: اسم إشارة + اسم + نعت
    if n == 3 and w1 in DEMOS \
            and pos[1] in NOUN_POS \
            and upos_list[2] == "ADJ":
        # demonstrative is indeclinable; the noun and adjective get damma
        demo    = w1
        noun_nf = w2 + "ُ"
        naat    = w3 + "ٌ"
        return f"""نوع الجملة: اسمية ثلاثية (اسم إشارة + خبر + نعت)
{demo}: اسم إشارة مبنيّ في محل رفع مبتدأ.
{noun_nf}: خبر مرفوع، وعلامة رفعه الضمة الظاهرة.
{naat}: نعت مرفوع يتبع الخبر في الإعراب، وعلامة رفعه الضمة الظاهرة."""

    # Rule X: ضمير منفصل + اسم + نعت/حال
    if n == 3 and w1 in DISJ_PRON \
         and pos[1] in NOUN_POS \
         and upos_list[2] == "ADJ":
        pron    = w1
        khbr    = w2 + "ُ"
        adj_nf  = w3 + "ٌ"
        return f"""نوع الجملة: اسمية ثلاثية (ضمير منفصل + خبر + نعت/حال)
{pron}: ضمير منفصل مبنيّ في محل رفع مبتدأ.
{khbr}: خبر مرفوع، وعلامة رفعه الضمة الظاهرة.
{adj_nf}: نعت/حال مرفوع يتبع الخبر في الإعراب، وعلامة رفعه الضمة الظاهرة."""

    # Rule X: كان + اسم + خبر
    if n == 3 and w1 == "كان" and pos[1] in NOUN_POS:
        verb_kan  = w1 + ""          # “كان” is indeclinable, no diacritic change
        subj_kan  = w2 + "ُ"         # damma on the اسم كان
        pred_kan  = w3 + "َ"         # fatha on the خبر كان
        return f"""نوع الجملة: اسمية ثلاثية (كان + اسم + خبر)
{verb_kan}: فعل ماضٍ ناقص مبنيّ على الفتح.
{subj_kan}: اسم كان مرفوع، وعلامة رفعه الضمة الظاهرة.
{pred_kan}: خبر كان منصوب، وعلامة نصبه الفتحة الظاهرة."""
    
    # Rule Y: إنّ + اسم + خبر
    if n == 3 \
        and upos_list[0] == "PART" \
        and w1 in {"إن", "ان"} \
        and pos[1] in NOUN_POS \
        and upos_list[2] == "ADJ":
        # Use the fully‐voweled form in the output
        particle_inn = "إنَّ"
        subj_inn     = w2 + "َ"  # نصب with fatha
        pred_inn     = w3 + "ٌ"  # رفع with damma
        return f"""نوع الجملة: اسمية ثلاثية (إنَّ + اسم + خبر)
{particle_inn}: حرف توكيد ونصب.
{subj_inn}: اسم إنَّ منصوب، وعلامة نصبه الفتحة الظاهرة.
{pred_inn}: خبر إنَّ مرفوع، وعلامة رفعه الضمة الظاهرة."""



    return "تعذر التعرف على التركيب وفق القوالب المحدّدة."   