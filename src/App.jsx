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
                  <p className="profile-role">Undergraduate Researcher</p>
                </div>
                <div className="cornell-badge">
                  <img src={cornellLogo} alt="Cornell University" className="cornell-logo-img" />
                </div>
              </div>
              <p className="profile-bio">
                I am an undergraduate researcher at Cornell University under Abe Davis.
                I do work in Signal Processing, HCI, and Computer Vision.
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
                  <div className="project-header">
                    <h3 className="project-title">
                      {project.link ? <a href={project.link}>{project.title}</a> : project.title}
                    </h3>
                    <span className="status-badge">{project.status}</span>
                  </div>
                  <p className="project-meta">{project.role}</p>

                  <div className="project-summary">
                    <p>{project.summary}</p>
                  </div>

                  <div className="tech-tags">
                    {project.tech.map((t, i) => (
                      <span key={i} className="tech-tag">{t}</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Engineering Section */}
        <section id="engineering" className="section">
          <div className="container">
            <h2 className="section-title">Engineering Projects</h2>
            <div className="grid grid-cols-1">
              {engineeringProjects.map((project, index) => (
                <div key={index} className="engineering-card">
                  <h3 className="engineering-title">{project.title}</h3>

                  <div className="project-summary">
                    <p>{project.summary}</p>
                  </div>

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
