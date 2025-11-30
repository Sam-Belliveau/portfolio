import React from 'react';
import profilePic from '../assets/profile.jpg';
import cornellLogo from '../assets/cornell-logo.svg';

const Header = ({ personalInfo }) => {
    return (
        <header className="header">
            <div className="container header_inner">
                <div className="profile">
                    <div className="profile_pic-container">
                        <img
                            src={profilePic}
                            alt="Profile"
                            className="profile_pic"
                        />
                    </div>
                    <div className="profile_info">
                        <div className="profile_header">
                            <div>
                                <h1 className="profile_name">{personalInfo.name}</h1>
                                <p className="profile_role">{personalInfo.title}</p>
                            </div>
                            <div className="profile_badge">
                                <img src={cornellLogo} alt="Cornell University" className="profile_badge-img" />
                            </div>
                        </div>
                        <p className="profile_bio">
                            {personalInfo.bio}
                        </p>
                        <div className="profile_links">
                            {personalInfo.links.map((link, index) => (
                                <a key={index} href={link.url} className="profile_link" target="_blank" rel="noopener noreferrer">
                                    <link.icon size={12} />
                                    {link.name}
                                </a>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </header>
    );
};

export default Header;
