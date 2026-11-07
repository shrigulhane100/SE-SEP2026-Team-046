import { Link } from 'react-router-dom';
import { motion } from 'motion/react';
import { Compass, Link2, TrendingUp, Target, Sparkles, GraduationCap, FlaskConical, Rocket, Briefcase, ShieldCheck, Clock, BarChart3 } from 'lucide-react';
import { Button, Card } from '../../components/ui';
import { MentorCard } from '../../components/common/Cards';
import { LoadingState } from '../../components/common/States';
import { useAsync } from '../../hooks/useAsync';
import { mentorService } from '../../services/mentorService';

const fade = { initial: { opacity: 0, y: 18 }, whileInView: { opacity: 1, y: 0 }, viewport: { once: true }, transition: { duration: 0.5 } };
const steps = [[Compass, 'Discover', 'Search mentors by guidance area, industry, experience and availability.'], [Link2, 'Connect', 'Send a short structured request. Mentors respond within 48 hours.'], [TrendingUp, 'Grow', 'Set goals, log activities and track your progress together.']];
const areas = [[Briefcase, 'Placements'], [GraduationCap, 'Higher Studies'], [FlaskConical, 'Research'], [Rocket, 'Entrepreneurship'], [Compass, 'Career Clarity']];
const why = [[ShieldCheck, 'Verified mentors', 'Every mentor profile is reviewed by the programme team.'], [Clock, 'Respectful of time', 'Capacity limits and 48-hour expiry keep requests manageable.'], [Target, 'Tracked progress', 'Goals, activities and feedback keep mentoring purposeful.'], [BarChart3, 'Privacy first', 'Admins see aggregate insights, never private mentoring notes.']];

export default function Landing() {
  const q = useAsync(() => mentorService.publicList({ limit: 3 }), []);
  return (
    <div>
      <section className="hero-bg">
        <div className="max-w-7xl mx-auto px-4 md:px-8 py-16 md:py-24 grid md:grid-cols-2 gap-12 items-center">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
            <span className="inline-block px-3 py-1 rounded-full bg-white/70 text-brand text-xs font-semibold mb-4">Find guidance. Build your future.</span>
            <h1 className="text-4xl md:text-6xl font-extrabold leading-[1.05]">Your next breakthrough starts with the right mentor.</h1>
            <p className="mt-5 text-lg text-gray-600 max-w-lg">Connect with experienced professionals, discover new opportunities and turn your ambitions into achievable goals.</p>
            <div className="mt-8 flex flex-wrap gap-3"><Link to="/explore"><Button size="lg">Explore Mentors</Button></Link><Link to="/register?role=MENTOR"><Button size="lg" variant="outline">Become a Mentor</Button></Link></div>
          </motion.div>
          <div className="relative h-[360px] hidden md:block" aria-hidden>
            <div className="absolute inset-x-6 inset-y-4 rounded-[48px] bg-gradient-to-br from-lav/60 via-pale to-peach/50 blur-sm" />
            {[['Career Guidance', Compass, 'top-2 left-0'], ['Skill Growth', Sparkles, 'top-36 right-0'], ['Goal Tracking', Target, 'bottom-4 left-12']].map(([t, Icon, pos], i) => (
              <motion.div key={t} animate={{ y: [0, -10, 0] }} transition={{ duration: 4 + i, repeat: Infinity, ease: 'easeInOut' }} className={`absolute ${pos} glass rounded-2xl px-5 py-4 flex items-center gap-3`}><span className="w-10 h-10 rounded-xl bg-brand text-white flex items-center justify-center"><Icon size={18} /></span><span className="font-head font-bold">{t}</span></motion.div>))}
          </div>
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-4 md:px-8 py-16">
        <motion.h2 {...fade} className="text-3xl font-extrabold text-center">How it works</motion.h2>
        <div className="grid md:grid-cols-3 gap-6 mt-10">{steps.map(([Icon, t, d], i) => <motion.div key={t} {...fade} transition={{ delay: i * 0.1, duration: 0.5 }}><Card className="h-full"><div className="w-12 h-12 rounded-2xl bg-pale text-brand flex items-center justify-center mb-4"><Icon /></div><div className="mono text-gray-400">0{i + 1}</div><h3 className="text-xl font-bold">{t}</h3><p className="text-gray-600 mt-1">{d}</p></Card></motion.div>)}</div>
      </section>

      <section className="max-w-7xl mx-auto px-4 md:px-8 pb-16">
        <div className="flex items-end justify-between mb-6"><div><h2 className="text-3xl font-extrabold">Featured mentors</h2><p className="text-gray-500 text-sm mt-1">Sample profiles for the prototype, not real people.</p></div><Link to="/explore" className="text-brand font-semibold text-sm">See all</Link></div>
        {q.loading ? <LoadingState rows={1} className="h-56" /> : <div className="grid md:grid-cols-3 gap-5">{(q.data || []).map((m) => <MentorCard key={m.id} m={m} to="/login" requestTo="/login" />)}</div>}
      </section>

      <section className="bg-white py-16"><div className="max-w-7xl mx-auto px-4 md:px-8">
        <h2 className="text-3xl font-extrabold text-center">Guidance areas</h2>
        <div className="flex flex-wrap justify-center gap-3 mt-8">{areas.map(([Icon, t]) => <span key={t} className="inline-flex items-center gap-2 px-5 py-3 rounded-2xl bg-ivory border border-black/5 font-semibold"><Icon size={18} className="text-brand" />{t}</span>)}</div>
        <p className="text-center text-sm text-gray-500 mt-4">Mentors also cover AI/ML, software development, VLSI and more.</p>
      </div></section>

      <section className="max-w-7xl mx-auto px-4 md:px-8 py-16">
        <h2 className="text-3xl font-extrabold text-center">Why Rock Starz</h2>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5 mt-10">{why.map(([Icon, t, d]) => <Card key={t}><Icon className="text-brand mb-3" /><h3 className="font-bold">{t}</h3><p className="text-sm text-gray-600 mt-1">{d}</p></Card>)}</div>
      </section>

      <section className="max-w-7xl mx-auto px-4 md:px-8 pb-16">
        <h2 className="text-3xl font-extrabold text-center">Experiences</h2><p className="text-center text-xs text-gray-500 mt-1">Sample quotes for illustration only.</p>
        <div className="grid md:grid-cols-2 gap-5 mt-8">{[['Sample student', 'The structured request made it easy to reach out. My mentor gave practical interview guidance.'], ['Sample mentor', 'Capacity limits let me guide a few students properly instead of many superficially.']].map(([w, t]) => <Card key={w}><p className="italic text-gray-700">“{t}”</p><div className="mt-3 text-sm font-semibold">{w}</div></Card>)}</div>
      </section>

      <section className="max-w-5xl mx-auto px-4 md:px-8 pb-8"><div className="rounded-section bg-gradient-to-br from-brand to-indigo2 text-white text-center p-10 md:p-14"><h2 className="text-3xl font-extrabold">Join the mentoring community</h2><p className="mt-2 text-white/80">Students find direction. Mentors give back. Together they grow.</p><div className="mt-6 flex justify-center gap-3 flex-wrap"><Link to="/register"><Button size="lg" className="bg-white !text-brand hover:bg-pale">Get Started</Button></Link><Link to="/login"><Button size="lg" variant="ghost" className="!text-white hover:bg-white/10">Login</Button></Link></div></div></section>
    </div>
  );
}
