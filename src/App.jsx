import React from 'react';
import { researchProjects, engineeringProjects, teachingExperience, industryExperience } from './data';
import profilePic from './assets/profile.jpg';
import cornellLogo from './assets/cornell-logo.svg';

function App() {
  return (
    <div className="app-container">
      {/* Header / Hero Section */}
      <header className="site-header">
        <div className="container header-inner">
          <div className="header-profile">
            <div className="profile-pic-container">
              <img
                src={profilePic}
                alt="Profile"
                className="profile-pic"
              />
            </div>
            <div className="profile-info">
              <div className="profile-header">
                <div>
                  <h1 className="profile-name">Sam Belliveau</h1>
                  <p className="profile-role">PhD Student in Computer Science</p>
                  <div className="cornell-badge">
                    <img src={cornellLogo} alt="Cornell University" className="cornell-logo-img" />
                    <span>Cornell University</span>
                  </div>
                </div>
                <nav className="nav-links">
                  <a href="#research">Research</a>
                  <a href="#engineering">Engineering</a>
                  <a href="#experience">Experience</a>
                </nav>
              </div>
              <p className="profile-bio">
                I am a researcher interested in systems, compilers, and programming languages.
                My work focuses on making software more reliable and efficient.
              </p>
            </div>
          </div>
        </div>
      </header>

      <main>
        {/* Research Section */}
        <section id="research" className="section bg-alt">
          <div className="container">
            <h2 className="section-title">Research</h2>
            <div className="project-list">
              {researchProjects.map((project, index) => (
                <div key={index} className="project-card">
                  <h3 className="project-title">
                    <a href={project.link}>{project.title}</a>
                  </h3>
                  <p className="project-meta">{project.venue} {project.year}</p>
                  <p className="project-description">{project.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Engineering Section */}
        <section id="engineering" className="section">
          <div className="container">
            <h2 className="section-title">Engineering Projects</h2>
            <div className="grid grid-cols-2">
              {engineeringProjects.map((project, index) => (
                <div key={index} className="engineering-card">
                  <h3 className="engineering-title">{project.title}</h3>
                  <p className="engineering-description">{project.description}</p>
                  <div className="tech-tags">
                    {project.tech.map((t, i) => (
                      <span key={i} className="tech-tag">
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Experience Section */}
        <section id="experience" className="section bg-alt">
          <div className="container">
            <div className="grid grid-cols-2">
              <div>
                <h2 className="section-title">Teaching</h2>
                <div className="experience-list">
                  {teachingExperience.map((exp, index) => (
                    <div key={index} className="experience-item">
                      <h4 className="experience-title">{exp.course}</h4>
                      <p className="experience-meta">{exp.institution} | {exp.role}</p>
                      <p className="experience-description">{exp.description}</p>
                    </div>
                  ))}
                </div>
              </div>
              <div>
                <h2 className="section-title">Industry</h2>
                <div className="experience-list">
                  {industryExperience.map((exp, index) => (
                    <div key={index} className="experience-item">
                      <h4 className="experience-title">{exp.company}</h4>
                      <p className="experience-meta">{exp.team} | {exp.role}</p>
                      <p className="experience-description">{exp.description}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="site-footer">
        <div className="container">
          <p>&copy; {new Date().getFullYear()} Sam Belliveau. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}

export default App;
