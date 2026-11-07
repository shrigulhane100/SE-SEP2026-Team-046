import { Link } from 'react-router-dom';
import { Button, Card } from '../../components/ui';
const Wrap = ({ title, intro, children }) => <div className="max-w-4xl mx-auto px-4 md:px-8 py-12"><h1 className="text-3xl md:text-4xl font-extrabold">{title}</h1><p className="text-gray-600 mt-3 text-lg">{intro}</p><div className="mt-8 grid gap-4">{children}</div></div>;
export const HowItWorks = () => (
  <Wrap title="How Rock Starz works" intro="From first request to completed mentoring in a few clear steps.">
    {[['Register and build your profile', 'Students share goals, skills and guidance areas. Mentors share expertise, capacity and availability. Mentors are verified by the programme team.'], ['Discover mentors', 'Search and filter by guidance area, industry, mentor type, experience and availability. Cards show a match indicator.'], ['Send a structured request', 'Pick a guidance area, describe what you need and your objective. Requests expire after 48 hours without a response.'], ['Mentor reviews and responds', 'Mentors see your context and accept or reject. Capacity limits protect mentor time.'], ['Mentor together', 'Set goals, log activities, pause or resume, then complete the relationship and share feedback.'], ['Programme insights', 'Administrators see aggregate participation data, never private conversations or notes.']].map(([t, d], i) => <Card key={t} className="flex gap-4"><div className="mono w-8 h-8 rounded-full bg-pale text-brand flex items-center justify-center shrink-0">{i + 1}</div><div><h3 className="font-bold">{t}</h3><p className="text-gray-600 text-sm mt-1">{d}</p></div></Card>)}
    <div className="text-center mt-4"><Link to="/register"><Button size="lg">Get Started</Button></Link></div>
  </Wrap>
);
export const About = () => (
  <Wrap title="About Rock Starz" intro="A student mentoring and career support platform built for IITM BS students, who study online from across India and often lack easy access to people with relevant career experience.">
    <Card><h3 className="font-bold">What we do</h3><p className="text-gray-600 text-sm mt-1">Rock Starz complements the existing IITM BS Mentor-Mentee Portal with career-based discovery, request handling, goal and activity tracking and programme insights.</p></Card>
    <Card><h3 className="font-bold">What mentoring includes</h3><p className="text-gray-600 text-sm mt-1">Guidance, feedback and perspective. It does not include referrals, placement guarantees or academic assessment.</p></Card>
    <Card><h3 className="font-bold">Team</h3><p className="text-gray-600 text-sm mt-1">Team Rock Starz · SE-SEP2026-Team-046. This is a prototype running on sample data.</p></Card>
  </Wrap>
);
