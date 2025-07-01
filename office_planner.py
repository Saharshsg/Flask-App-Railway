from app import create_app, db
from app.models import User, Schedule

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Schedule': Schedule}

if __name__ == '__main__':
    # Start the scheduler only when running the app directly (not during flask commands)
    from app.scheduler import scheduler
    if not app.debug and not app.testing:
        scheduler.start()
        app.logger.info("Scheduler started.")
    
    app.run(debug=True) 