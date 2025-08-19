CREATE TRIGGER notify_changes AFTER INSERT ON ventas
FOR EACH ROW EXECUTE FUNCTION pg_notify('data_changes', json_build_object('table', 'ventas', 'data', row_to_json(NEW)));