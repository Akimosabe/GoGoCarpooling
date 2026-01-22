import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'

export function ProfileSettings() {
  return (
    <div className="mx-auto max-w-xl px-4 py-8">
      <Card>
        <h1 className="mb-4 text-xl font-bold text-slate-900">Настройки</h1>
        <p className="text-slate-600">
          Раздел в разработке. Восстановление пароля доступно на странице входа.
        </p>
        <Link to="/profile" className="mt-4 inline-block">
          <Button variant="outline" size="sm">
            ← В личный кабинет
          </Button>
        </Link>
      </Card>
    </div>
  )
}
