import React from 'react';

interface AdminPanelProps {
    onAddPrerequisite: (prerequisite: any) => void;
    onManageUsers: () => void;
}

export const AdminPanel: React.FC<AdminPanelProps> = ({ onAddPrerequisite, onManageUsers }) => {
    return (
        <div className="admin-panel">
            <h2>Admin Panel</h2>
            <section className="prerequisites-management">
                {/* Prerequisites management UI */}
            </section>
            <section className="user-management">
                {/* User management UI */}
            </section>
        </div>
    );
};
