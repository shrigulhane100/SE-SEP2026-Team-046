export const PageHeader = ({ title, sub, actions }) => (
  <div className="mb-6 flex flex-wrap items-end justify-between gap-3"><div><h1 className="text-2xl md:text-3xl font-extrabold">{title}</h1>{sub && <p className="text-gray-500 mt-1">{sub}</p>}</div>{actions}</div>
);
export const Section = ({ title, action, children, className = '' }) => (
  <section className={className}><div className="flex items-center justify-between mb-3"><h2 className="text-lg font-bold">{title}</h2>{action}</div>{children}</section>
);
