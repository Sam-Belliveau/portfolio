import { Fragment } from 'react';
import {
  education,
  experience,
  honors,
  news,
  profile,
  projects,
  publications,
} from './content';

// Spacing is Tailwind's, surfaces and corners are the bevel system's, and the
// two never overlap: nothing here rounds a corner or draws an edge.
const CARD = 'surface mb-2 flex gap-2 p-2 last:mb-0';

const Plate = ({ className, src, alt, loading }) => (
  <span className={`plate ${className}`}>
    <img src={src} alt={alt} loading={loading} />
  </span>
);

const Logo = ({ src, alt }) => (
  <img
    className="m-2 size-20 shrink-0 self-center object-contain"
    src={src}
    alt={alt}
    loading="lazy"
  />
);

// A surface needs three layers -- masked face, multiply, screen -- and a pair of
// pseudo-elements only gives two. This is the middle one.
const Shade = () => <span className="shade" aria-hidden="true" />;

// The figures already carry white margins, so letting the plate fill the card's
// full height and centring the figure on that white reads as one white field
// rather than a short image floating in a tall card.
const Figure = ({ src, alt }) => (
  <Plate className="thumbnail w-56 shrink-0 self-stretch" src={src} alt={alt} loading="lazy" />
);

const Intro = () => (
  <header className="intro surface mb-2 flex items-start gap-2 p-2">
    <Shade />
    <div className="m-2 min-w-0 flex-1">
      <h1 className="text-4xl tracking-tight">{profile.name}</h1>
      <p className="mt-1 mb-2 text-left italic text-stone-500">{profile.headline}</p>
      <nav className="mb-4">
        {profile.links.map(({ label, href }, index) => (
          <Fragment key={label}>
            {index > 0 && ' · '}
            <a href={href}>{label}</a>
          </Fragment>
        ))}
      </nav>
      {profile.bio}
    </div>
    <Plate className="portrait w-44 shrink-0" src={profile.photo} alt={profile.name} />
  </header>
);

const Section = ({ title, children }) => (
  <section className="surface mb-2 p-2">
    <Shade />
    <h2 className="m-2 mb-3 text-2xl">{title}</h2>
    {children}
  </section>
);

const DatedList = ({ items }) => (
  <ul className="m-0 list-none p-0">
    {items.map(({ date, text }, index) => (
      <li key={index} className={`${CARD} items-center`}>
        <Shade />
        <span className="m-2 w-28 shrink-0 whitespace-nowrap text-stone-500">{date}</span>
        <span className="m-2 min-w-0 flex-1">{text}</span>
      </li>
    ))}
  </ul>
);

const TitleLine = ({ title, href, dates }) => (
  <h3 className="mb-0.5 flex items-baseline justify-between gap-4 text-lg">
    <span>{href ? <a href={href}>{title}</a> : title}</span>
    {dates && <span className="shrink-0 text-sm text-stone-500">{dates}</span>}
  </h3>
);

const AuthorList = ({ authors }) =>
  authors.map((author, index) => (
    <Fragment key={author}>
      {index > 0 && ', '}
      {author === profile.citationName ? <strong className="text-stone-800">{author}</strong> : author}
    </Fragment>
  ));

const Publication = ({ title, authors, venue, note, thumbnail }) => (
  <article className={CARD}>
    <Shade />
    {thumbnail && <Figure src={thumbnail} alt={title} />}
    <div className="m-2 min-w-0 flex-1">
      <TitleLine title={title} />
      <p className="mb-1 text-left text-stone-500">
        <AuthorList authors={authors} />
      </p>
      <p className="mb-0">
        <em>{venue}</em>. {note}
      </p>
    </div>
  </article>
);

const Project = ({ title, dates, href, description, tech, thumbnail }) => (
  <article className={CARD}>
    <Shade />
    {thumbnail && <Figure src={thumbnail} alt={title} />}
    <div className="m-2 min-w-0 flex-1">
      <TitleLine title={title} href={href} dates={dates} />
      <p className="mb-1">{description}</p>
      <p className="mb-0 text-left text-sm italic text-stone-500">{tech.join(' · ')}</p>
    </div>
  </article>
);

const Position = ({ organization, logo, role, dates, summary }) => (
  <article className={CARD}>
    <Shade />
    {logo && <Logo src={logo} alt={organization} />}
    <div className="m-2 min-w-0 flex-1">
      <TitleLine title={organization} dates={dates} />
      <p className="mb-1 text-left text-stone-500">{role}</p>
      <p className="mb-0">{summary}</p>
    </div>
  </article>
);

const Degree = ({ school, logo, degree, dates }) => (
  <article className={CARD}>
    <Shade />
    {logo && <Logo src={logo} alt={school} />}
    <div className="m-2 min-w-0 flex-1 self-center">
      <TitleLine title={school} dates={dates} />
      <p className="mb-0 text-left text-stone-500">{degree}</p>
    </div>
  </article>
);

const App = () => (
  <div className="mx-auto max-w-4xl px-6 pt-6 pb-4">
    <Intro />
    <main>
      <Section title="News">
        <DatedList items={news} />
      </Section>
      <Section title="Publications">
        {publications.map((publication) => (
          <Publication key={publication.title} {...publication} />
        ))}
      </Section>
      <Section title="Selected Projects">
        {projects.map((project) => (
          <Project key={project.title} {...project} />
        ))}
      </Section>
      <Section title="Experience">
        {experience.map((position) => (
          <Position key={position.organization + position.role} {...position} />
        ))}
      </Section>
      <Section title="Education">
        {education.map((degree) => (
          <Degree key={degree.school + degree.degree} {...degree} />
        ))}
      </Section>
      <Section title="Honors">
        <DatedList items={honors} />
      </Section>
    </main>
    <footer className="mt-4 text-sm text-stone-500">
      © {new Date().getFullYear()} {profile.name}
    </footer>
  </div>
);

export default App;
