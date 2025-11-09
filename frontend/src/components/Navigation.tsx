/**
 * Navigation component.
 */

import { Link, useLocation } from 'react-router-dom';

export function Navigation() {
  const location = useLocation();

  const navItems = [
    { path: '/orders', label: 'Pedidos' },
    { path: '/campaigns', label: 'Campanhas' },
    { path: '/customers', label: 'Clientes' },
  ];

  return (
    <nav
      style={{
        backgroundColor: 'white',
        borderBottom: '1px solid #e0e0e0',
        padding: '0 20px',
        position: 'sticky',
        top: 0,
        zIndex: 100,
      }}
    >
      <div className="container" style={{ display: 'flex', alignItems: 'center', height: '64px' }}>
        <Link
          to="/"
          style={{
            fontSize: '20px',
            fontWeight: '600',
            color: 'var(--primary-red)',
            textDecoration: 'none',
            marginRight: '40px',
          }}
        >
          Analytics do Restaurante
        </Link>
        <div style={{ display: 'flex', gap: '8px' }}>
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              style={{
                padding: '8px 16px',
                borderRadius: '6px',
                textDecoration: 'none',
                color: location.pathname === item.path ? 'white' : 'var(--black)',
                backgroundColor: location.pathname === item.path ? 'var(--primary-red)' : 'transparent',
                fontWeight: location.pathname === item.path ? '600' : '400',
                transition: 'all 0.2s',
              }}
            >
              {item.label}
            </Link>
          ))}
        </div>
      </div>
    </nav>
  );
}

