from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


DATABASE_URL = (
    "postgresql+psycopg2://postgres:password@localhost:5432/ai_ecosystem"
)


engine = create_engine(DATABASE_URL)

Session = sessionmaker(bind=engine)


def create_table():
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS students (
                id SERIAL PRIMARY KEY,
                name VARCHAR(50),
                age INTEGER,
                major VARCHAR(100)
            )
        """))
        conn.commit()

    print("Create table students success")


def insert_data():
    with Session() as session:
        session.execute(text("""
            INSERT INTO students(name, age, major)
            VALUES ('Oat', 22, 'AI Engineering')
        """))
        session.commit()

    print("Insert data success")


def show_data():
    with Session() as session:
        result = session.execute(
            text("SELECT * FROM students")
        )

        for row in result:
            print(row)


def update_data():
    with Session() as session:
        session.execute(text("""
            UPDATE students
            SET age = 23
            WHERE name='Oat'
        """))
        session.commit()

    print("Update data success")


def delete_data():
    with Session() as session:
        session.execute(text("""
            DELETE FROM students
            WHERE name='Oat'
        """))
        session.commit()

    print("Delete data success")


def delete_table():
    with engine.connect() as conn:
        conn.execute(
            text("DROP TABLE IF EXISTS students")
        )
        conn.commit()

    print("Delete table success")


if __name__ == "__main__":

    create_table()

    insert_data()
    print("\nAfter Insert:")
    show_data()

    update_data()
    print("\nAfter Update:")
    show_data()

    delete_data()
    print("\nAfter Delete:")
    show_data()

    delete_table()