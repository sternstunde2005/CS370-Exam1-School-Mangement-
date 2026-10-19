BEGIN TRANSACTION;
CREATE TABLE absences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            module_name TEXT DEFAULT NULL,
            count INTEGER DEFAULT 0,
            total_hours INTEGER DEFAULT 0,
            academic_year TEXT DEFAULT '2024-2025',
            semester TEXT DEFAULT '1',
            FOREIGN KEY (student_id) REFERENCES users (id)
        );
INSERT INTO "absences" VALUES(1,1,'Mathematics',2,4,'2024-2025','1');
INSERT INTO "absences" VALUES(2,1,'Databases',1,2,'2024-2025','1');
INSERT INTO "absences" VALUES(3,2,'Mathematics',12,24,'2024-2025','1');
INSERT INTO "absences" VALUES(4,2,'Databases',8,16,'2024-2025','1');
INSERT INTO "absences" VALUES(5,3,'Mathematics',0,0,'2024-2025','1');
INSERT INTO "absences" VALUES(6,3,'Databases',1,2,'2024-2025','1');
CREATE TABLE classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            academic_year TEXT DEFAULT '2024-2025',
            teacher_name TEXT
        );
INSERT INTO "classes" VALUES(1,'Computer Science 101','2024-2025','Dr. Taylor');
CREATE TABLE grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            module_name TEXT NOT NULL,
            grade REAL NOT NULL,
            teacher_name TEXT,
            academic_year TEXT DEFAULT '2024-2025',
            semester TEXT DEFAULT '1',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES users (id)
        );
INSERT INTO "grades" VALUES(1,1,'Mathematics',15.5,'Dr. Taylor','2024-2025','1','2026-10-18 19:38:42');
INSERT INTO "grades" VALUES(2,1,'Databases',13.0,'Dr. Rivera','2024-2025','1','2026-10-18 19:38:42');
INSERT INTO "grades" VALUES(3,2,'Mathematics',9.0,'Dr. Taylor','2024-2025','1','2026-10-18 19:38:42');
INSERT INTO "grades" VALUES(4,2,'Databases',11.5,'Dr. Rivera','2024-2025','1','2026-10-18 19:38:42');
INSERT INTO "grades" VALUES(5,3,'Mathematics',17.0,'Dr. Taylor','2024-2025','1','2026-10-18 19:38:42');
INSERT INTO "grades" VALUES(6,3,'Databases',16.0,'Dr. Rivera','2024-2025','1','2026-10-18 19:38:42');
CREATE TABLE risk_thresholds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            min_grade REAL DEFAULT 10.0,
            max_absences INTEGER DEFAULT 10,
            risk_level TEXT DEFAULT 'medium'
        );
INSERT INTO "risk_thresholds" VALUES(1,10.0,10,'medium');
CREATE TABLE student_class (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            class_id INTEGER NOT NULL,
            FOREIGN KEY (student_id) REFERENCES users (id),
            FOREIGN KEY (class_id) REFERENCES classes (id)
        );
INSERT INTO "student_class" VALUES(1,1,1);
INSERT INTO "student_class" VALUES(2,2,1);
INSERT INTO "student_class" VALUES(3,3,1);
CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        );
INSERT INTO "users" VALUES(1,'Alex Demo','alex.demo@example.test','cb2433073edb25ca77f0445dcdbd7e7c568196eef1cd54da7228ddd227240e2e','student');
INSERT INTO "users" VALUES(2,'Morgan Example','morgan.example@example.test','cb2433073edb25ca77f0445dcdbd7e7c568196eef1cd54da7228ddd227240e2e','student');
INSERT INTO "users" VALUES(3,'Jamie Sample','jamie.sample@example.test','cb2433073edb25ca77f0445dcdbd7e7c568196eef1cd54da7228ddd227240e2e','student');
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES('risk_thresholds',1);
INSERT INTO "sqlite_sequence" VALUES('users',3);
INSERT INTO "sqlite_sequence" VALUES('classes',1);
INSERT INTO "sqlite_sequence" VALUES('student_class',3);
INSERT INTO "sqlite_sequence" VALUES('grades',6);
INSERT INTO "sqlite_sequence" VALUES('absences',6);
COMMIT;
