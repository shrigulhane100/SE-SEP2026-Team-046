import { Bar, BarChart, CartesianGrid, Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { Card } from '../../components/ui';
const STATUS = { PENDING: '#D9A441', ACCEPTED: '#2F9E6E', REJECTED: '#D14B4B', EXPIRED: '#9CA3AF', CANCELLED: '#CBD5E1' };
const tip = { contentStyle: { borderRadius: 12, border: '1px solid #eee', fontSize: 12 } };
export const ChartCard = ({ title, sub, children, className = '' }) => <Card className={className}><h3 className="font-bold">{title}</h3>{sub && <p className="text-xs text-gray-500 mb-2">{sub}</p>}<div className="h-64 mt-2">{children}</div></Card>;
export const RegistrationsChart = ({ data }) => (
  <ResponsiveContainer><BarChart data={data}><CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#eee" /><XAxis dataKey="month" tickLine={false} axisLine={false} fontSize={12} /><YAxis allowDecimals={false} tickLine={false} axisLine={false} fontSize={12} width={28} /><Tooltip {...tip} /><Legend iconType="circle" wrapperStyle={{ fontSize: 12 }} /><Bar dataKey="students" name="Students" fill="#8274D8" radius={[6, 6, 0, 0]} /><Bar dataKey="mentors" name="Mentors" fill="#397F78" radius={[6, 6, 0, 0]} /></BarChart></ResponsiveContainer>
);
export const StatusDonut = ({ data }) => {
  const d = data.filter((x) => x.value > 0);
  return <ResponsiveContainer><PieChart><Pie data={d} dataKey="value" nameKey="name" innerRadius={55} outerRadius={85} paddingAngle={2}>{d.map((x) => <Cell key={x.name} fill={STATUS[x.name]} />)}</Pie><Tooltip {...tip} /><Legend iconType="circle" wrapperStyle={{ fontSize: 12 }} formatter={(v) => v[0] + v.slice(1).toLowerCase()} /></PieChart></ResponsiveContainer>;
};
export const HBar = ({ data, color = '#435A79' }) => (
  <ResponsiveContainer><BarChart data={data} layout="vertical" margin={{ left: 8 }}><CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#eee" /><XAxis type="number" allowDecimals={false} tickLine={false} axisLine={false} fontSize={12} /><YAxis type="category" dataKey="name" width={130} tickLine={false} axisLine={false} fontSize={12} /><Tooltip {...tip} /><Bar dataKey="value" name="Count" fill={color} radius={[0, 6, 6, 0]} /></BarChart></ResponsiveContainer>
);
