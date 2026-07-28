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

const Intro = () => (
  <header className="intro">
    <div>
      <h1>{profile.name}</h1>
      <p className="headline">{profile.headline}</p>
      <nav className="contact-links">
        {profile.links.map(({ label, href }, index) => (
          <Fragment key={label}>
            {index > 0 && ' · '}
            <a href={href}>{label}</a>
          </Fragment>
        ))}
      </nav>
      {profile.bio}
    </div>
    <img className="portrait" src={profile.photo} alt={profile.name} />
  </header>
);

const Section = ({ title, children }) => (
  <section>
    <h2>{title}</h2>
    {children}
  </section>
);

const DatedList = ({ items }) => (
  <ul className="dated-list">
    {items.map(({ date, text }, index) => (
      <li key={index}>
        <span className="date">{date}</span>
        <span>{text}</span>
      </li>
    ))}
  </ul>
);

const TitleLine = ({ title, href, dates }) => (
  <h3>
    <span>{href ? <a href={href}>{title}</a> : title}</span>
    {dates && <span className="dates">{dates}</span>}
  </h3>
);

const AuthorList = ({ authors }) =>
  authors.map((author, index) => (
    <Fragment key={author}>
      {index > 0 && ', '}
      {author === profile.citationName ? <strong>{author}</strong> : author}
    </Fragment>
  ));

const Publication = ({ title, authors, venue, note, thumbnail }) => (
  <article className="entry">
    {thumbnail && <img className="thumbnail" src={thumbnail} alt={title} loading="lazy" />}
    <div>
      <TitleLine title={title} />
      <p className="byline">
        <AuthorList authors={authors} />
      </p>
      <p>
        <em>{venue}</em>. {note}
      </p>
    </div>
  </article>
);

const Project = ({ title, dates, href, description, tech, thumbnail }) => (
  <article className="entry">
    {thumbnail && <img className="thumbnail" src={thumbnail} alt={title} loading="lazy" />}
    <div>
      <TitleLine title={title} href={href} dates={dates} />
      <p>{description}</p>
      <p className="tech">{tech.join(' · ')}</p>
    </div>
  </article>
);

const Position = ({ organization, role, dates, summary }) => (
  <article className="position">
    <TitleLine title={organization} dates={dates} />
    <p className="byline">{role}</p>
    <p>{summary}</p>
  </article>
);

const Degree = ({ school, degree, dates }) => (
  <article className="position">
    <TitleLine title={school} dates={dates} />
    <p className="byline">{degree}</p>
  </article>
);

const App = () => (
  <div className="page">
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
    <footer>
      © {new Date().getFullYear()} {profile.name}
    </footer>
  </div>
);

export default App;
