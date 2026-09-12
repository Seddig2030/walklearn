# -*- coding: utf-8 -*-
"""
WalkLearn — نسخة Python/Kivy شخصية تعمل بدون Node.js وبدون سيرفر.
البيانات محفوظة محليًا، والنطق يستخدم Android TextToSpeech عند توفره.
"""
import json, os
from datetime import date, timedelta
from kivy.config import Config
Config.set("kivy", "exit_on_escape", "0")

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.clock import Clock

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
except Exception:
    arabic_reshaper = None
    get_display = None

ROOT = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(ROOT, "NotoSansArabic-Regular.ttf")

with open(os.path.join(ROOT, "curriculum.json"), "r", encoding="utf-8") as f:
    DATA = json.load(f)
LEVELS = DATA["levels"]
LABELS = DATA["labels"]
LESSONS = DATA["lessons"]

PLACEMENT = [
    {"en":"She ___ a teacher.","options":["is","am","are","be"],"answer":0},
    {"en":"They ___ from Jordan.","options":["is","am","are","was"],"answer":2},
    {"en":"I ___ to the market yesterday.","options":["go","goes","went","going"],"answer":2},
    {"en":"By the time we arrived, the film ___ already started.","options":["has","have","had","was"],"answer":2},
    {"en":"If I ___ more time, I would learn more.","options":["have","had","has","will have"],"answer":1},
    {"en":"The report ___ written by the research team.","options":["is","was","did","has"],"answer":1},
    {"en":"\"Ostensibly\" is closest in meaning to:","options":["secretly","apparently","rarely","urgently"],"answer":1},
    {"en":"If I ___ studied harder, I would have passed.","options":["have","had","has","did"],"answer":1},
]

def ar(text):
    """Arabic shaping for Kivy/SDL when the optional packages are installed."""
    if not isinstance(text, str) or not text:
        return text
    if arabic_reshaper and get_display and any("\u0600" <= c <= "\u06ff" for c in text):
        try:
            return get_display(arabic_reshaper.reshape(text))
        except Exception:
            pass
    return text

def speak(text):
    try:
        from jnius import autoclass
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        TextToSpeech = autoclass("android.speech.tts.TextToSpeech")
        Locale = autoclass("java.util.Locale")
        activity = PythonActivity.mActivity
        app = App.get_running_app()
        if not hasattr(app, "_tts"):
            app._tts = TextToSpeech(activity, None)
        app._tts.setLanguage(Locale.US)
        app._tts.setSpeechRate(0.9)
        app._tts.speak(text, TextToSpeech.QUEUE_FLUSH, None, "walklearn")
    except Exception:
        # على جهاز غير أندرويد أو إذا لم تتوفر TTS، لا نوقف التطبيق.
        pass

def level_for_score(n):
    if n <= 1: return "A1"
    if n <= 3: return "A2"
    if n <= 5: return "B1"
    if n <= 6: return "B2"
    return "C1"

def store_path():
    app = App.get_running_app()
    return os.path.join(app.user_data_dir, "progress.json")

def load_progress():
    default = {"level":None,"completed":[],"streak":0,"last":None,"xp":0}
    try:
        with open(store_path(),"r",encoding="utf-8") as f:
            default.update(json.load(f))
    except Exception:
        pass
    return default

def save_progress(s):
    os.makedirs(os.path.dirname(store_path()), exist_ok=True)
    with open(store_path(),"w",encoding="utf-8") as f:
        json.dump(s,f,ensure_ascii=False,indent=2)

def complete_lesson(lesson_id, quiz_score):
    s=load_progress()
    if lesson_id not in s["completed"]:
        s["completed"].append(lesson_id)
        s["xp"] += 50 + quiz_score*10
    today=date.today()
    ts=today.isoformat()
    if s["last"] != ts:
        ys=(today-timedelta(days=1)).isoformat()
        s["streak"] = s["streak"]+1 if s["last"]==ys else 1
        s["last"]=ts
    save_progress(s)
    return s

class Base(Screen):
    def make(self):
        root=BoxLayout(orientation="vertical",padding=dp(14),spacing=dp(8))
        scroll=ScrollView(do_scroll_x=False)
        content=BoxLayout(orientation="vertical",spacing=dp(8),size_hint_y=None)
        content.bind(minimum_height=content.setter("height"))
        scroll.add_widget(content)
        root.add_widget(scroll)
        return root,content

    def add_label(self,c,text,size=16):
        x=Label(text=ar(text),font_name=FONT if os.path.exists(FONT) else "Roboto",
                color=(.94,.94,.94,1),font_size=f"{size}sp",halign="right",
                valign="middle",text_size=(Window.width-dp(30),None),
                size_hint_y=None)
        x.bind(texture_size=lambda inst,val:setattr(inst,"height",val[1]+dp(12)))
        c.add_widget(x); return x

    def btn(self,text,fn,primary=False):
        b=Button(text=ar(text),font_name=FONT if os.path.exists(FONT) else "Roboto",
                 size_hint_y=None,height=dp(50),background_normal="",
                 background_color=(.85,.62,.12,1) if primary else (.12,.12,.14,1),
                 color=(.05,.05,.05,1) if primary else (.94,.94,.94,1))
        b.bind(on_release=lambda *_:fn())
        return b

class Landing(Base):
    def on_pre_enter(self):
        self.clear_widgets(); root,c=self.make()
        self.add_label(c,"WalkLearn",29)
        self.add_label(c,"تعلّم الإنجليزية بطريقتك — تطبيق شخصي بدون حساب وبدون سيرفر.",19)
        self.add_label(c,"اختبار تحديد مستوى، دروس A1 → C1، مفردات، حفظ، كتابة، قواعد، قراءة، استماع واختبارات.",15)
        c.add_widget(self.btn("ابدأ اختبار تحديد المستوى",lambda:setattr(self.manager,"current","placement"),True))
        c.add_widget(self.btn("أعرف مستواي — ادخل للدروس",lambda:setattr(self.manager,"current","lessons")))
        self.add_label(c,"النسخة الجديدة لا تحتاج npm أو Next.js. كل المحتوى داخل التطبيق.",13)
        self.add_widget(root)

class Placement(Base):
    def on_pre_enter(self):
        self.step=0; self.correct=0; self.render()
    def render(self):
        self.clear_widgets(); root,c=self.make(); q=PLACEMENT[self.step]
        self.add_label(c,f"اختبار تحديد المستوى — سؤال {self.step+1} من {len(PLACEMENT)}",14)
        self.add_label(c,q["en"],21)
        for i,o in enumerate(q["options"]):
            c.add_widget(self.btn(o,lambda i=i:self.answer(i)))
        self.add_widget(root)
    def answer(self,i):
        if i==PLACEMENT[self.step]["answer"]: self.correct+=1
        if self.step+1>=len(PLACEMENT):
            s=load_progress(); s["level"]=level_for_score(self.correct); save_progress(s)
            self.manager.get_screen("dashboard").refresh(); self.manager.current="dashboard"
        else:
            self.step+=1; self.render()

class Dashboard(Base):
    def on_pre_enter(self): self.refresh()
    def refresh(self):
        self.clear_widgets(); root,c=self.make(); s=load_progress(); lvl=s["level"]
        if not lvl:
            self.manager.current="landing"; return
        ls=[x for x in LESSONS if x["level"]==lvl]
        done=sum(x["id"] in s["completed"] for x in ls)
        nxt=next((x for x in ls if x["id"] not in s["completed"]),None)
        self.add_label(c,"WalkLearn — لوحة التعلم",26)
        self.add_label(c,f"مستواك: {LABELS[lvl]} ({lvl})",19)
        self.add_label(c,f"🔥 السلسلة: {s['streak']} يوم  •  ⭐ XP: {s['xp']}  •  أكملت {done}/{len(ls)}",14)
        if lvl in ("B2","C1"): self.add_label(c,"🎓 مسار الجاهزية الجامعية مفعّل.",14)
        if nxt:
            self.add_label(c,"درسك التالي:",14); self.add_label(c,nxt["titleAr"],19)
            c.add_widget(self.btn("ابدأ الدرس",lambda l=nxt:self.open(l),True))
        else:
            self.add_label(c,"🎉 أكملت مستوىك الحالي. انتقل للمستوى التالي من صفحة الدروس.",16)
        c.add_widget(self.btn("كل الدروس",lambda:setattr(self.manager,"current","lessons")))
        c.add_widget(self.btn("تقدمي",lambda:setattr(self.manager,"current","progress")))
        self.add_widget(root)
    def open(self,l): self.manager.get_screen("lesson").start(l); self.manager.current="lesson"

class Lessons(Base):
    def on_pre_enter(self):
        self.level=load_progress()["level"] or "A1"; self.render()
    def render(self):
        self.clear_widgets(); root,c=self.make()
        self.add_label(c,"الدروس",25)
        row=BoxLayout(size_hint_y=None,height=dp(46),spacing=dp(4))
        for lvl in LEVELS:
            b=Button(text=lvl,background_normal="",background_color=(.85,.62,.12,1) if lvl==self.level else (.12,.12,.14,1))
            b.bind(on_release=lambda _,x=lvl:self.choose(x)); row.add_widget(b)
        c.add_widget(row)
        for l in [x for x in LESSONS if x["level"]==self.level]:
            done=l["id"] in load_progress()["completed"]
            title=("🎓 " if l.get("academic") else "")+l["titleAr"]+("  ✓" if done else "")
            c.add_widget(self.btn(title,lambda l=l:self.open(l)))
        c.add_widget(self.btn("⌂ لوحة التعلم",lambda:setattr(self.manager,"current","dashboard")))
        self.add_widget(root)
    def choose(self,lvl): self.level=lvl; self.render()
    def open(self,l): self.manager.get_screen("lesson").start(l); self.manager.current="lesson"

class Lesson(Base):
    def start(self,l):
        self.lesson=l; self.stage="vocab"; self.i=0; self.qi=0; self.score=0; self.queue=list(range(len(l["vocab"]))); self.revealed=False
        self.render()
    def render(self):
        self.clear_widgets(); root,c=self.make()
        c.add_widget(self.btn("← رجوع للدروس",lambda:setattr(self.manager,"current","lessons")))
        self.add_label(c,self.lesson["titleAr"],23)
        if self.stage=="vocab": self.vocab(c)
        elif self.stage=="memorize": self.memorize(c)
        elif self.stage=="writing": self.writing(c)
        elif self.stage=="grammar": self.grammar(c)
        elif self.stage=="reading": self.reading(c)
        elif self.stage=="quiz": self.quiz(c)
        else: self.done(c)
        self.add_widget(root)
    def next(self,text,fn): return self.btn(text,fn,True)
    def vocab(self,c):
        self.add_label(c,"المفردات والنطق",14)
        for v in self.lesson["vocab"]:
            self.add_label(c,f"{v['en']}  —  {v['ar']}",18)
            self.add_label(c,v["example"],13); self.add_label(c,v["exampleAr"],12)
            c.add_widget(self.btn("🔊 نطق",lambda t=v["en"]:speak(t)))
        c.add_widget(self.next("التالي: الحفظ",lambda:self.set_stage("memorize")))
    def memorize(self,c):
        if not self.queue:
            self.add_label(c,"🎉 حفظت كل كلمات الدرس.",18); c.add_widget(self.next("التالي: تمرين الكتابة",lambda:self.set_stage("writing"))); return
        v=self.lesson["vocab"][self.queue[0]]
        self.add_label(c,f"باقي {len(self.queue)} كلمة",13); self.add_label(c,v["ar"],22)
        if self.revealed:
            self.add_label(c,v["en"],27); c.add_widget(self.btn("🔊 استمع",lambda t=v["en"]:speak(t)))
            c.add_widget(self.btn("حفظتها ✓",self.remembered,True)); c.add_widget(self.btn("لسا ما حفظتها",self.repeat))
        else: c.add_widget(self.next("👁️ اكشف الكلمة",lambda:self.reveal()))
    def reveal(self): self.revealed=True; self.render()
    def remembered(self): self.queue.pop(0); self.revealed=False; self.render()
    def repeat(self): self.queue.append(self.queue.pop(0)); self.revealed=False; self.render()
    def writing(self,c):
        v=self.lesson["vocab"][self.i]; self.write_checked=False
        self.add_label(c,f"تمرين الكتابة {self.i+1} من {len(self.lesson['vocab'])}",13)
        self.add_label(c,f"اكتب الكلمة الإنجليزية لـ: {v['ar']}",19)
        inp=TextInput(multiline=False,halign="center",font_size="20sp",size_hint_y=None,height=dp(54))
        c.add_widget(inp)
        msg=self.add_label(c,"",14)
        def check():
            if self.write_checked: return
            if inp.text.strip().lower()==v["en"].strip().lower():
                msg.text=ar("صح! ✓"); msg.color=(.5,.9,.7,1)
            else:
                msg.text=ar(f"الصحيح: {v['en']}"); msg.color=(1,.4,.35,1)
            self.write_checked=True
            button.text=ar("التالي")
        button=self.next("تحقق",check); c.add_widget(button)
        self.add_label(c,"يمكنك الضغط على تحقق ثم الانتقال للكلمة التالية.",12)
        # prevent the stage from being skipped before checking
        def advance():
            if not self.write_checked:
                check(); return
            self.i+=1
            if self.i>=len(self.lesson["vocab"]): self.set_stage("grammar")
            else: self.render()
        button.unbind(on_release=button._fbind if False else None) if False else None
        # Replace binding cleanly
        for ev in list(button.get_property_observers("on_release")):
            pass
        button.unbind(on_release=check)
        button.bind(on_release=lambda *_:advance())
    def grammar(self,c):
        self.add_label(c,self.lesson["grammarTitleAr"],19); self.add_label(c,self.lesson["grammarNoteAr"],14)
        for ex in self.lesson["grammarExamples"]:
            self.add_label(c,ex["en"],17); self.add_label(c,ex["ar"],13); c.add_widget(self.btn("🔊",lambda t=ex["en"]:speak(t)))
        c.add_widget(self.next("التالي",lambda:self.set_stage("reading" if self.lesson.get("reading") else "quiz")))
    def reading(self,c):
        r=self.lesson["reading"]; self.add_label(c,r["titleAr"],19); self.add_label(c,r["en"],15); self.add_label(c,r["ar"],13)
        c.add_widget(self.btn("🔊 استمع للفقرة",lambda:speak(r["en"])))
        c.add_widget(self.next("التالي: الاختبار",lambda:self.set_stage("quiz")))
    def quiz(self,c):
        q=self.lesson["quiz"][self.qi]; self.add_label(c,f"سؤال {self.qi+1} من {len(self.lesson['quiz'])}",13); self.add_label(c,q["promptAr"],18)
        for i,o in enumerate(q["options"]): c.add_widget(self.btn(o,lambda i=i:self.answer(i)))
    def answer(self,i):
        if i==self.lesson["quiz"][self.qi]["answerIndex"]: self.score+=1
        self.qi+=1
        if self.qi>=len(self.lesson["quiz"]): self.set_stage("done")
        else: self.render()
    def done(self,c):
        self.add_label(c,"أحسنت! 🎉",28); self.add_label(c,f"نتيجتك: {self.score} من {len(self.lesson['quiz'])}",19)
        c.add_widget(self.next("حفظ التقدم والعودة للدروس",self.finish))
    def finish(self): complete_lesson(self.lesson["id"],self.score); self.manager.current="lessons"
    def set_stage(self,s): self.stage=s; self.render()

class Progress(Base):
    def on_pre_enter(self): self.render()
    def render(self):
        self.clear_widgets(); root,c=self.make(); s=load_progress(); lvl=s["level"]
        self.add_label(c,"تقدمي",25)
        self.add_label(c,f"المستوى: {LABELS[lvl]+' ('+lvl+')' if lvl else 'لم يُحدد'}",17)
        self.add_label(c,f"🔥 أيام متتالية: {s['streak']}",15)
        self.add_label(c,f"⭐ نقاط XP: {s['xp']}",15)
        self.add_label(c,f"الدروس المكتملة: {len(s['completed'])} من {len(LESSONS)}",15)
        self.add_label(c,"كل شيء محفوظ محليًا داخل التطبيق. لا يوجد حساب ولا خادم.",13)
        c.add_widget(self.btn("إعادة ضبط التقدم",self.reset))
        c.add_widget(self.btn("⌂ لوحة التعلم",lambda:setattr(self.manager,"current","dashboard")))
        self.add_widget(root)
    def reset(self): save_progress({"level":None,"completed":[],"streak":0,"last":None,"xp":0}); self.render()

class WalkLearn(App):
    def build(self):
        Window.clearcolor=(.035,.035,.04,1)
        sm=ScreenManager()
        for cls,name in [(Landing,"landing"),(Placement,"placement"),(Dashboard,"dashboard"),(Lessons,"lessons"),(Lesson,"lesson"),(Progress,"progress")]:
            sm.add_widget(cls(name=name))
        s=load_progress()
        sm.current="dashboard" if s["level"] else "landing"
        return sm

if __name__=="__main__":
    WalkLearn().run()
