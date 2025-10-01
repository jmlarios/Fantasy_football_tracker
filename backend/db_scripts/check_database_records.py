import sys
from pathlib import Path
from sqlalchemy import text, inspect
from datetime import datetime
import logging

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.append(str(src_path))

from config import SessionLocal, engine
import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_database_records():
    """Comprehensive check of all database records and schema."""
    
    db = SessionLocal()
    try:
        print("=" * 80)
        print("🔍 DATABASE RECORDS CHECK")
        print("=" * 80)
        print(f"⏰ Check performed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 1. Check database connection
        print("📡 Testing database connection...")
        try:
            db.execute(text("SELECT 1"))
            print("✅ Database connection successful")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
        print()
        
        # 2. List all existing tables
        print("📋 Existing tables:")
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if not tables:
            print("❌ No tables found in database")
            return False
        
        for table in sorted(tables):
            print(f"  - {table}")
        print(f"📊 Total tables: {len(tables)}")
        print()
        
        # 3. Check table schemas and record counts
        print("📈 Table details:")
        print("-" * 60)
        
        table_stats = {}
        
        for table in sorted(tables):
            try:
                # Get record count
                result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                table_stats[table] = count
                
                # Get column info
                columns = inspector.get_columns(table)
                column_names = [col['name'] for col in columns]
                
                print(f"🗂️  {table.upper()}")
                print(f"   📊 Records: {count:,}")
                print(f"   🏗️  Columns: {len(column_names)}")
                print(f"   📝 Fields: {', '.join(column_names[:5])}" + 
                      (f" (+{len(column_names)-5} more)" if len(column_names) > 5 else ""))
                
                # Show sample data if records exist
                if count > 0 and count <= 5:
                    sample_result = db.execute(text(f"SELECT * FROM {table} LIMIT 3"))
                    samples = sample_result.fetchall()
                    if samples:
                        print(f"   📄 Sample: {len(samples)} records shown")
                elif count > 0:
                    print(f"   📄 Sample: (showing first 3 of {count} records)")
                    sample_result = db.execute(text(f"SELECT * FROM {table} LIMIT 3"))
                    samples = sample_result.fetchall()
                
                print()
                
            except Exception as e:
                print(f"   ❌ Error checking {table}: {e}")
                print()
        
        # 4. Summary statistics
        print("=" * 60)
        print("📊 DATABASE SUMMARY")
        print("=" * 60)
        
        total_records = sum(table_stats.values())
        print(f"🗃️  Total tables: {len(tables)}")
        print(f"📈 Total records: {total_records:,}")
        print()
        
        print("📋 Records by table:")
        for table, count in sorted(table_stats.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_records * 100) if total_records > 0 else 0
            print(f"   {table:<20} {count:>8,} ({percentage:5.1f}%)")
        print()
        
        # 5. Check for transfer-related columns (to see if migration is needed)
        print("🔧 MIGRATION READINESS CHECK")
        print("-" * 40)
        
        migration_needed = []
        
        # Check if transfer_history table exists
        if 'transfer_history' not in tables:
            migration_needed.append("❌ transfer_history table missing")
        else:
            print("✅ transfer_history table exists")
        
        # Check if fantasy_teams has total_budget column
        if 'fantasy_teams' in tables:
            ft_columns = [col['name'] for col in inspector.get_columns('fantasy_teams')]
            if 'total_budget' not in ft_columns:
                migration_needed.append("❌ fantasy_teams.total_budget column missing")
            else:
                print("✅ fantasy_teams.total_budget column exists")
        
        # Check if players has price column
        if 'players' in tables:
            player_columns = [col['name'] for col in inspector.get_columns('players')]
            if 'price' not in player_columns:
                migration_needed.append("❌ players.price column missing")
            else:
                print("✅ players.price column exists")
        
        # Check if matchdays has free_transfers column
        if 'matchdays' in tables:
            md_columns = [col['name'] for col in inspector.get_columns('matchdays')]
            if 'free_transfers' not in md_columns:
                migration_needed.append("❌ matchdays.free_transfers column missing")
            else:
                print("✅ matchdays.free_transfers column exists")
        
        if migration_needed:
            print()
            print("⚠️  MIGRATION REQUIRED:")
            for issue in migration_needed:
                print(f"   {issue}")
            print()
            print("🔧 Run: docker-compose exec backend python migrate_transfers.py")
        else:
            print("✅ All transfer-related schema is ready!")
        print()
        
        # 6. Check specific data quality
        print("🔍 DATA QUALITY CHECKS")
        print("-" * 40)
        
        # Check users
        if 'users' in tables and table_stats.get('users', 0) > 0:
            active_users = db.execute(text("SELECT COUNT(*) FROM users WHERE is_active = true")).scalar()
            print(f"👤 Active users: {active_users}/{table_stats['users']}")
        
        # Check players
        if 'players' in tables and table_stats.get('players', 0) > 0:
            active_players = db.execute(text("SELECT COUNT(*) FROM players WHERE is_active = true")).scalar()
            print(f"⚽ Active players: {active_players}/{table_stats['players']}")
            
            # Check positions distribution
            try:
                pos_result = db.execute(text("""
                    SELECT position, COUNT(*) as count 
                    FROM players 
                    WHERE is_active = true 
                    GROUP BY position 
                    ORDER BY count DESC
                """))
                positions = pos_result.fetchall()
                if positions:
                    print("   Position distribution:", end="")
                    for pos, count in positions:
                        print(f" {pos}:{count}", end="")
                    print()
            except:
                pass
        
        # Check fantasy teams
        if 'fantasy_teams' in tables and table_stats.get('fantasy_teams', 0) > 0:
            teams_with_players = db.execute(text("""
                SELECT COUNT(DISTINCT fantasy_team_id) 
                FROM fantasy_team_players
            """)).scalar() if 'fantasy_team_players' in tables else 0
            print(f"🏆 Teams with players: {teams_with_players}/{table_stats['fantasy_teams']}")
        
        # Check matchdays
        if 'matchdays' in tables and table_stats.get('matchdays', 0) > 0:
            active_matchdays = db.execute(text("SELECT COUNT(*) FROM matchdays WHERE is_active = true")).scalar()
            finished_matchdays = db.execute(text("SELECT COUNT(*) FROM matchdays WHERE is_finished = true")).scalar()
            print(f"📅 Matchdays: {active_matchdays} active, {finished_matchdays} finished, {table_stats['matchdays']} total")
        
        print()
        print("=" * 80)
        print("✅ DATABASE CHECK COMPLETE")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"❌ Error during database check: {e}")
        print(f"Error details: {traceback.format_exc()}")
        return False
    finally:
        db.close()

def check_specific_table(table_name: str, limit: int = 10):
    """Check a specific table in detail."""
    
    db = SessionLocal()
    try:
        print(f"🔍 Detailed check for table: {table_name}")
        print("-" * 50)
        
        # Check if table exists
        inspector = inspect(engine)
        if table_name not in inspector.get_table_names():
            print(f"❌ Table '{table_name}' does not exist")
            return False
        
        # Get table schema
        columns = inspector.get_columns(table_name)
        print(f"📋 Schema for {table_name}:")
        for col in columns:
            nullable = "NULL" if col['nullable'] else "NOT NULL"
            default = f"DEFAULT {col['default']}" if col['default'] else ""
            print(f"   {col['name']:<20} {str(col['type']):<15} {nullable:<8} {default}")
        print()
        
        # Get record count
        count = db.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
        print(f"📊 Total records: {count}")
        
        if count > 0:
            # Show sample data
            result = db.execute(text(f"SELECT * FROM {table_name} LIMIT {limit}"))
            rows = result.fetchall()
            column_names = result.keys()
            
            print(f"📄 Sample data (showing {len(rows)} of {count} records):")
            print("-" * 100)
            
            # Print header
            header = " | ".join(f"{name:<15}" for name in column_names[:6])
            print(header)
            print("-" * len(header))
            
            # Print rows
            for row in rows:
                row_data = " | ".join(f"{str(val):<15}" for val in row[:6])
                print(row_data)
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ Error checking table {table_name}: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Check database records and schema")
    parser.add_argument("--table", help="Check specific table in detail")
    parser.add_argument("--limit", type=int, default=10, help="Limit for sample data")
    
    args = parser.parse_args()
    
    if args.table:
        check_specific_table(args.table, args.limit)
    else:
        check_database_records()
