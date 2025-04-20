const express = require('express');
const cors = require('cors');
const bcrypt = require('bcrypt');
const app = express();

// Middleware
app.use(cors());
app.use(express.json());

// MySQL Connection
var mysql = require('mysql2');
var db = mysql.createConnection({
    host: process.env.DB_HOST || '127.0.0.1',
    user: process.env.DB_USER || 'root',
    password: process.env.DB_PASSWORD || 'Root',
    database: process.env.DB_NAME || 'textai_db'
});

// Test the connection
db.connect(function(err) {
    if (err) {
        console.error('Error connecting to MySQL: ' + err.stack);
        return;
    }
    console.log('Connected to MySQL as id ' + db.threadId);
});

// Registration endpoint
app.post('/api/register', async (req, res) => {
    try {
        const { username, password } = req.body;

        // Validate input
        if (!username || !password) {
            return res.status(400).json({ error: 'Username and password are required' });
        }

        // Hash password
        const hashedPassword = await bcrypt.hash(password, 10);

        // Insert user into database
        const query = 'INSERT INTO users (username, password) VALUES (?, ?)';
        db.query(query, [username, hashedPassword], (err, results) => {
            if (err) {
                if (err.code === 'ER_DUP_ENTRY') {
                    return res.status(400).json({ 
                        error: 'Username already exists' 
                    });
                }
                console.error('Database error:', err);
                return res.status(500).json({ error: 'Server error during registration' });
            }

            res.status(201).json({
                message: 'Registration successful',
                user: {
                    id: results.insertId,
                    username
                }
            });
        });
    } catch (error) {
        console.error('Registration error:', error);
        res.status(500).json({ error: 'Server error during registration' });
    }
});

// Login endpoint
app.post('/api/login', async (req, res) => {
    try {
        const { username, password } = req.body;

        // Validate input
        if (!username || !password) {
            return res.status(400).json({ error: 'Username and password are required' });
        }

        // Find user
        const query = 'SELECT * FROM users WHERE username = ?';
        db.query(query, [username], async (err, results) => {
            if (err) {
                console.error('Database error:', err);
                return res.status(500).json({ error: 'Server error during login' });
            }

            if (results.length === 0) {
                return res.status(404).json({ 
                    error: 'User does not exist',
                    redirect: false
                });
            }

            const user = results[0];

            // Check password
            const validPassword = await bcrypt.compare(password, user.password);
            if (!validPassword) {
                return res.status(401).json({ 
                    error: 'Invalid password',
                    redirect: false
                });
            }

            res.json({
                message: 'Login successful',
                user: {
                    id: user.id,
                    username: user.username,
                    created_at: user.created_at
                },
                redirect: true,
                redirectUrl: '/home.html'
            });
        });
    } catch (error) {
        console.error('Login error:', error);
        res.status(500).json({ 
            error: 'Server error during login',
            redirect: false
        });
    }
});

// Use a different port (3001 instead of 3000 since 3000 is in use)
const PORT = 3001;
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});

